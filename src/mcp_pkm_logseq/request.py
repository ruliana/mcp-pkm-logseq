import os
import time
import logging
from functools import wraps
from typing import Callable, TypeVar, Any, Dict, List, Optional, Union
from requests import post, Response
from requests.exceptions import HTTPError, RequestException, Timeout, ConnectionError
from mcp.shared.exceptions import McpError
from mcp.types import INTERNAL_ERROR, ErrorData

# Set up logging
logger = logging.getLogger(__name__)

# Type variables for the retry decorator
T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])

# Constants for retry configuration
DEFAULT_MAX_RETRIES = 3
DEFAULT_BASE_DELAY = 1  # Base delay in seconds
DEFAULT_BACKOFF_FACTOR = 2  # Exponential backoff multiplier
DEFAULT_TIMEOUT = 10  # Request timeout in seconds

# HTTP status codes that should trigger a retry
RETRY_STATUS_CODES = {429, 500, 502, 503, 504}


def with_retry(
    max_retries: int = DEFAULT_MAX_RETRIES,
    base_delay: float = DEFAULT_BASE_DELAY,
    backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
    retry_on_status_codes: set = RETRY_STATUS_CODES,
    retry_on_exceptions: tuple = (ConnectionError, Timeout, HTTPError)
) -> Callable[[F], F]:
    """
    Decorator that adds retry logic with exponential backoff to functions.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries in seconds
        backoff_factor: Multiplier for the delay on each successive retry
        retry_on_status_codes: Set of HTTP status codes that should trigger a retry
        retry_on_exceptions: Tuple of exception types that should trigger a retry
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            attempt = 0
            last_exception = None
            last_status_code = None
            response = None

            while attempt < max_retries + 1:  # Changed <= to < to fix attempt count
                try:
                    attempt += 1
                    logger.debug(f"Request attempt {attempt}/{max_retries + 1}")
                    
                    result = func(*args, **kwargs)
                    
                    # For functions that return Response objects, check status code
                    if isinstance(result, Response) and result.status_code in retry_on_status_codes:
                        last_status_code = result.status_code
                        logger.warning(f"Received status code {result.status_code}, eligible for retry")
                        
                        # If we've reached max retries, raise the appropriate exception
                        if attempt > max_retries:
                            break
                        
                        # Calculate backoff time
                        delay = base_delay * (backoff_factor ** (attempt - 1))
                        logger.info(f"Retrying in {delay:.2f}s (attempt {attempt}/{max_retries})")
                        time.sleep(delay)
                        continue
                    
                    # Success case
                    return result
                    
                except retry_on_exceptions as e:
                    last_exception = e
                    
                    # Check if the exception is HTTPError - we need special handling
                    if isinstance(e, HTTPError) and e.response is not None:
                        response = e.response
                        status_code = response.status_code
                        
                        # Only retry on specific status codes
                        if status_code not in retry_on_status_codes:
                            # For 401, we have a special error message
                            if status_code == 401:
                                raise McpError(ErrorData(code=INTERNAL_ERROR, message="Invalid API token"))
                            
                            # For other 4xx errors (except 429), we don't retry
                            if 400 <= status_code < 500 and status_code != 429:
                                raise McpError(
                                    ErrorData(code=INTERNAL_ERROR, message=f"API request failed: {str(e)}")
                                )
                            # For non-retriable status codes, raise immediately
                            logger.error(f"Request failed with non-retriable status code: {status_code}")
                            raise McpError(
                                ErrorData(code=INTERNAL_ERROR, message=f"API request failed: {str(e)}")
                            )
                    
                    logger.warning(f"Request failed with retriable exception: {str(e)}")
                    
                    # Calculate backoff time
                    delay = base_delay * (backoff_factor ** (attempt - 1))
                    logger.info(f"Retrying in {delay:.2f}s (attempt {attempt}/{max_retries})")
                    time.sleep(delay)
                    
                except Exception as e:
                    # Non-retriable exception, raise immediately
                    logger.error(f"Request failed with non-retriable exception: {str(e)}")
                    raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Request failed: {str(e)}"))

            # If we get here, all retries failed
            if last_exception:
                if isinstance(last_exception, ConnectionError) or isinstance(last_exception, Timeout):
                    error_type = "Network error" if isinstance(last_exception, ConnectionError) else "Timeout error"
                    logger.error(f"{error_type} persisted after {attempt} attempts: {str(last_exception)}")
                    raise McpError(
                        ErrorData(code=INTERNAL_ERROR, 
                                 message=f"{error_type}: {str(last_exception)} (after {attempt} attempts)")
                    )
                elif isinstance(last_exception, HTTPError) and last_exception.response is not None:
                    status_code = last_exception.response.status_code
                    logger.error(f"HTTP error with status {status_code} persisted after {attempt} attempts")
                    raise McpError(
                        ErrorData(code=INTERNAL_ERROR,
                                 message=f"API request failed with status {status_code} (after {attempt} attempts)")
                    )
                # Re-raise other exceptions
                raise McpError(
                    ErrorData(code=INTERNAL_ERROR, message=f"Request failed: {str(last_exception)} (after {attempt} attempts)")
                )
            elif last_status_code:
                logger.error(f"Status code {last_status_code} persisted after {attempt} attempts")
                raise McpError(
                    ErrorData(code=INTERNAL_ERROR,
                             message=f"API request failed with status {last_status_code} (after {attempt} attempts)")
                )
            
            # This should not happen, but just in case
            raise McpError(
                ErrorData(code=INTERNAL_ERROR, message=f"Request failed with unknown error after {attempt} attempts")
            )
        
        return wrapper
    
    return decorator


def request(method: str, *args: list) -> dict:
    """
    Make authenticated request to Logseq API with retry capability.
    
    This function will automatically retry on transient failures like network
    errors, timeouts, and server errors (5xx) using exponential backoff.
    
    Args:
        method: The Logseq API method to call
        *args: Arguments to pass to the Logseq API method
        
    Returns:
        The JSON response from the Logseq API
        
    Raises:
        McpError: If the request fails after all retry attempts
    """
    return _request_with_retry(method, *args)


@with_retry(
    max_retries=DEFAULT_MAX_RETRIES,
    base_delay=DEFAULT_BASE_DELAY,
    backoff_factor=DEFAULT_BACKOFF_FACTOR
)
def _request_with_retry(method: str, *args: list) -> dict:
    """Internal function that performs the actual request with retry capability."""
    api_key = os.getenv("LOGSEQ_API_TOKEN")
    if not api_key:
        api_key = os.getenv("LOGSEQ_API_KEY")
    if not api_key:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message="No API token found. Add it to your environment variables using LOGSEQ_API_TOKEN"))

    logseq_url = os.getenv("LOGSEQ_URL", "http://localhost:12315")

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"method": method, "args": args}

    response = post(f"{logseq_url}/api", headers=headers, json=payload, timeout=DEFAULT_TIMEOUT)
    
    # Handle non-retry status codes immediately
    if response.status_code == 401:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message="Invalid API token"))
    
    # Handle other 4xx errors (except 429)
    if 400 <= response.status_code < 500 and response.status_code != 429:
        raise McpError(
            ErrorData(code=INTERNAL_ERROR, message=f"API request failed with status {response.status_code}")
        )
    
    # For retry-eligible status codes, raise an exception that will be caught by the decorator
    if response.status_code in RETRY_STATUS_CODES:
        response.raise_for_status()
        
    # For successful responses and any we didn't explicitly handle above, validate and return
    response.raise_for_status()
    return response.json()