import os
from mcp.server.fastmcp import FastMCP
from mcp.shared.exceptions import McpError, ErrorData
from mcp.types import INTERNAL_ERROR, ErrorData
from requests import post
from requests.exceptions import HTTPError, RequestException
from mcp_pkm_logseq.markdown_converter import page_to_markdown

from pprint import pprint


mcp = FastMCP("MCP PKM Logseq")


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


@mcp.resource("logseq://start")
def start() -> str:
    """Initial instructions on how to interact with this knowledge base. Before any other interaction, read this first."""
    return request("logseq.Editor.getPage", "MCP PKM Logseq")


@mcp.resource("logseq://page/{name}")
def page(name: str) -> str:
    """Get a page from Logseq"""
    return request("logseq.Editor.getPage", name, True)


def request(method: str, *args: list) -> dict:
    """Make authenticated request to Logseq API."""

    api_key = os.getenv("LOGSEQ_API_KEY", "this-is-my-logseq-mcp-token")
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


if __name__ == "__main__":
    # rslt = request("logseq.Editor.getPage", "MCP PKM Logseq")
    # print(rslt)
    # print("=" * 100)
    rslt = request("logseq.DB.q", "[[MCP PKM Logseq]]")
    pprint(rslt)
    print("=" * 100)
    rslt = page_to_markdown(rslt)
    print(rslt)
