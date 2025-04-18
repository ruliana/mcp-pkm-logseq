import os
import pytest
import requests_mock
import time
from requests.exceptions import ConnectionError, Timeout, RequestException
from unittest.mock import patch, call
from mcp_pkm_logseq.request import request
from mcp.shared.exceptions import McpError
from mcp.types import INTERNAL_ERROR


@pytest.fixture
def mock_env_vars(monkeypatch):
    monkeypatch.setenv("LOGSEQ_API_KEY", "test_api_key")
    monkeypatch.setenv("LOGSEQ_URL", "http://test-logseq.com")


def test_request_success(mock_env_vars, requests_mock):
    # Setup mock response
    mock_response = {"result": "test page content"}
    requests_mock.post(
        "http://test-logseq.com/api",
        json=mock_response,
        status_code=200
    )

    # Call the function
    result = request("logseq.Editor.getPage", "test-page")

    # Verify the request was made correctly
    assert requests_mock.called
    assert requests_mock.last_request.headers["Authorization"] == "Bearer test_api_key"
    assert requests_mock.last_request.headers["Content-Type"] == "application/json"
    assert requests_mock.last_request.json() == {
        "method": "logseq.Editor.getPage",
        "args": ["test-page"]
    }
    assert result == {"result": "test page content"}


def test_request_unauthorized(mock_env_vars, requests_mock):
    # Setup mock response for unauthorized error
    requests_mock.post(
        "http://test-logseq.com/api",
        status_code=401
    )

    # Verify the correct exception is raised
    with pytest.raises(McpError) as exc_info:
        request("logseq.Editor.getPage", "test-page")
    
    assert "Invalid API token" in str(exc_info.value)


def test_request_http_error(mock_env_vars, requests_mock):
    # Setup mock response for other HTTP error
    requests_mock.post(
        "http://test-logseq.com/api",
        status_code=500
    )

    # Verify the correct exception is raised
    with pytest.raises(McpError) as exc_info:
        request("logseq.Editor.getPage", "test-page")
    
    assert "API request failed" in str(exc_info.value)


def test_request_network_error(mock_env_vars, requests_mock):
    # Setup mock to raise a network error
    requests_mock.post(
        "http://test-logseq.com/api",
        exc=ConnectionError("Network error")
    )

    # Verify the correct exception is raised
    with pytest.raises(McpError) as exc_info:
        request("logseq.Editor.getPage", "test-page")
    
    assert "Network error" in str(exc_info.value)


# Tests for retry functionality
def test_retry_on_network_error_success(mock_env_vars, requests_mock):
    """Test that transient network errors trigger retries and eventually succeed."""
    # Setup mock to fail twice with connection error, then succeed
    mock_response = {"result": "test page content"}
    
    # Use a counter to track request attempts
    attempts = {'count': 0}
    
    def response_callback(request, context):
        attempts['count'] += 1
        if attempts['count'] <= 2:  # Fail the first 2 attempts
            raise ConnectionError("Temporary network error")
        # Succeed on the 3rd attempt
        return mock_response
    
    requests_mock.post(
        "http://test-logseq.com/api",
        json=response_callback
    )
    
    # Call the function
    result = request("logseq.Editor.getPage", "test-page")
    
    # Verify retries were made and we got the eventual success
    assert attempts['count'] == 3  # Should have tried 3 times
    assert result == mock_response


def test_retry_on_timeout_success(mock_env_vars, requests_mock):
    """Test that timeout errors trigger retries and eventually succeed."""
    # Setup mock to fail twice with timeout error, then succeed
    mock_response = {"result": "test page content"}
    
    # Use a counter to track request attempts
    attempts = {'count': 0}
    
    def response_callback(request, context):
        attempts['count'] += 1
        if attempts['count'] <= 2:  # Fail the first 2 attempts
            raise Timeout("Request timed out")
        # Succeed on the 3rd attempt
        return mock_response
    
    requests_mock.post(
        "http://test-logseq.com/api",
        json=response_callback
    )
    
    # Call the function
    result = request("logseq.Editor.getPage", "test-page")
    
    # Verify retries were made and we got the eventual success
    assert attempts['count'] == 3  # Should have tried 3 times
    assert result == mock_response


def test_retry_on_server_error_success(mock_env_vars, requests_mock):
    """Test that 5xx errors trigger retries and eventually succeed."""
    # Setup mock to return 503, 502, then 200
    mock_response = {"result": "test page content"}
    
    # Define responses for each attempt
    responses = [
        {'status_code': 503, 'json': {'error': 'Service unavailable'}},
        {'status_code': 502, 'json': {'error': 'Bad gateway'}},
        {'status_code': 200, 'json': mock_response}
    ]
    
    # Use a counter to track request attempts
    attempts = {'count': 0}
    
    def response_callback(request, context):
        resp = responses[attempts['count']]
        context.status_code = resp['status_code']
        attempts['count'] += 1
        return resp['json']
    
    requests_mock.post(
        "http://test-logseq.com/api",
        json=response_callback
    )
    
    # Call the function
    result = request("logseq.Editor.getPage", "test-page")
    
    # Verify retries were made and we got the eventual success
    assert attempts['count'] == 3  # Should have tried 3 times
    assert result == mock_response


def test_retry_max_attempts_failure(mock_env_vars, requests_mock):
    """Test that the function gives up after max retries and returns an error."""
    # Setup mock to always fail with network error
    requests_mock.post(
        "http://test-logseq.com/api",
        exc=ConnectionError("Persistent network error")
    )
    
    # Call the function - should raise an error after max retries
    with pytest.raises(McpError) as exc_info:
        request("logseq.Editor.getPage", "test-page")
    
    # Should indicate this was after retries
    assert "Network error" in str(exc_info.value)
    assert "after 4 attempts" in str(exc_info.value)


def test_retry_backoff_timing(mock_env_vars, requests_mock):
    """Test that exponential backoff is correctly implemented."""
    # Setup mock to always fail with connection error
    requests_mock.post(
        "http://test-logseq.com/api",
        exc=ConnectionError("Network error")
    )
    
    # Mock sleep function to verify backoff timing
    with patch('time.sleep') as mock_sleep:
        # Call the function - should raise an error after max retries
        with pytest.raises(McpError):
            request("logseq.Editor.getPage", "test-page")
        
        # Check that sleep was called with increasing durations
        # With default backoff factor of a=2, should be roughly 1s, 2s (a*1s)
        expected_calls = [
            call(1),  # First retry after 1 second
            call(2),  # Second retry after 2 seconds (2¹ * base_delay)
        ]
        mock_sleep.assert_has_calls(expected_calls)


def test_no_retry_on_client_error(mock_env_vars, requests_mock):
    """Test that client errors (4xx except 429) don't trigger retries."""
    # Setup mock for 400 error
    requests_mock.post(
        "http://test-logseq.com/api",
        status_code=400,
        json={'error': 'Bad request'}
    )
    
    # Call the function - should raise immediately without retrying
    with patch('time.sleep') as mock_sleep:
        with pytest.raises(McpError) as exc_info:
            request("logseq.Editor.getPage", "test-page")
        
        # Sleep should not have been called (no retries)
        mock_sleep.assert_not_called()
    
    assert "API request failed" in str(exc_info.value)
    assert "after 3 attempts" not in str(exc_info.value)


def test_retry_on_rate_limit(mock_env_vars, requests_mock):
    """Test that rate limit errors (429) trigger retries."""
    # Setup mock to return 429 twice, then 200
    mock_response = {"result": "test page content"}
    
    # Define responses for each attempt
    responses = [
        {'status_code': 429, 'json': {'error': 'Too many requests'}},
        {'status_code': 429, 'json': {'error': 'Too many requests'}},
        {'status_code': 200, 'json': mock_response}
    ]
    
    # Use a counter to track request attempts
    attempts = {'count': 0}
    
    def response_callback(request, context):
        resp = responses[attempts['count']]
        context.status_code = resp['status_code']
        attempts['count'] += 1
        return resp['json']
    
    requests_mock.post(
        "http://test-logseq.com/api",
        json=response_callback
    )
    
    # Call the function
    result = request("logseq.Editor.getPage", "test-page")
    
    # Verify retries were made and we got the eventual success
    assert attempts['count'] == 3  # Should have tried 3 times
    assert result == mock_response