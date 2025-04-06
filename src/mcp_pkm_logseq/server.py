import asyncio
from mcp.server.fastmcp import FastMCP
from mcp_pkm_logseq.to_markdown import page_to_markdown
from mcp_pkm_logseq.request import request


mcp = FastMCP("MCP PKM Logseq")


def main() -> None:
    """Start the MCP server."""
    mcp.run()


@mcp.resource("logseq://guide")
def guide() -> str:
    """Initial instructions on how to interact with this knowledge base. Before any other interaction, read this first."""
    return req("logseq.DB.q", '(page "MCP PKM Logseq")')


@mcp.tool()
def personal_notes(topics: list[str]) -> str:
    """Retrieve personal notes from Logseq.

    Use this to find relavant information about a specific topic or about user preferences.
    It will return all information that is tagged with the topics from the user's personal
    knowledge base.

    The information is returned in markdown format, each item in the list is a separate
    unit of information. Hierachical information is returned as a nested list.

    The returning markdown contains text in double square brackets, like this:
    `[[topic]]`. These are links to other topics, you can follow them to get more
    information.

    Args:
        topics: A list of topics to search for. Topics are case-insensitive. If no topic
        is provided, the tool will return the guide on how to use the personal knowledge
        base.

    Returns:
        A markdown formatted string containing the information with the given topics.
        Empty if no information is found.
    """
    if len(topics) > 0:
        formatted_topics = [f'[[{topic}]]' for topic in topics]
        formatted_topics = " ".join(formatted_topics)
        rslt = req("logseq.DB.q", f'(or {formatted_topics})')

        # If the topic is not found by tag, try to find via full text search.
        if rslt == "":
            formatted_topics = [f'"{topic}"' for topic in topics]
            formatted_topics = " ".join(formatted_topics)
            rslt = req("logseq.DB.q", f'(or {formatted_topics})')

        return rslt

    return guide()


def req(method: str, *args: list) -> str:
    """Make authenticated request to Logseq API and convert the response to markdown."""
    return page_to_markdown(request(method, *args))