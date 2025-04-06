import os
from requests import post
from requests.exceptions import HTTPError, RequestException
from mcp.shared.exceptions import McpError
from mcp.types import INTERNAL_ERROR, ErrorData


def request(method: str, *args: list) -> dict:
    """Make authenticated request to Logseq API."""

    api_key = os.getenv("LOGSEQ_API_KEY")
    logseq_url = os.getenv("LOGSEQ_URL", "http://localhost:12315")

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"method": method, "args": args}

    try:
        response = post(f"{logseq_url}/api", headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except HTTPError as e:
        if response.status_code == 401:
            raise McpError(ErrorData(code=INTERNAL_ERROR, message="Invalid API token"))
        raise McpError(
            ErrorData(code=INTERNAL_ERROR, message=f"API request failed: {str(e)}")
        )
    except RequestException as e:
        raise McpError(
            ErrorData(code=INTERNAL_ERROR, message=f"Network error: {str(e)}")
        )