import os
from mcp.server.fastmcp import FastMCP
from mcp.shared.exceptions import McpError, ErrorData
from mcp.types import INTERNAL_ERROR, ErrorData
from requests import post
from requests.exceptions import HTTPError, RequestException
from mcp_pkm_logseq.to_markdown import page_to_markdown, clean_response

from pprint import pprint


mcp = FastMCP("MCP PKM Logseq")


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


@mcp.resource("logseq://start")
def start() -> str:
    """Initial instructions on how to interact with this knowledge base. Before any other interaction, read this first."""
    return req("logseq.DB.q", '(page "MCP PKM Logseq")')


@mcp.resource("logseq://page/{name}")
def page(name: str) -> str:
    """Get a page from Logseq

    Use this to get the content of a page.

    Args:
        name: The name of the page to get. Name is case-insensitive.

    Returns:
        A markdown formatted string containing the content of the page. Empty if the
        page does not exist.
    """
    return req("logseq.DB.q", f'(page "{name}")')


@mcp.tool()
def get_tagged_blocks(*tags: list[str]) -> str:
    """Get all blocks with any of the given tags.

    Use this to find relavant information about a specific topic. A tag can also be a
    page name, in which case all blocks that refer to that page are returned.

    A "block", in Logseq, is an atomic unit of content. It can contain text, images,
    checklists, code, and more.
    
    Args:
        tags: A list of tags to search for. Tags are case-insensitive.

    Returns:
        A markdown formatted string containing the blocks with the given tags. Empty
        if no blocks are found.
    """
    if len(tags) == 0:
        return ""

    if len(tags) == 1:
        return req("logseq.DB.q", f'[[{tags[0]}]]')

    return req("logseq.DB.q", f'[[{" OR ".join(tags)}]]')


def req(method: str, *args: list) -> str:
    """Make authenticated request to Logseq API and convert the response to markdown."""
    return page_to_markdown(request(method, *args))


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


# if __name__ == "__main__":
#     rslt = get_tagged_blocks("query")
#     print(rslt)
