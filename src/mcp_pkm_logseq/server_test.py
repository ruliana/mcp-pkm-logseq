import os
import pytest
import requests_mock
from requests.exceptions import ConnectionError
from mcp_pkm_logseq.server import request
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