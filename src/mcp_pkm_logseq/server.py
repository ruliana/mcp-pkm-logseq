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


def date_range_to_query(query: str, from_date: str = None, to_date: str = None) -> str:
    """Convert a date range to a logseq query string."""

    if from_date and to_date:
        return f"(and {query} (between {from_date} {to_date}))"
    elif from_date:
        return f"(and {query} (between -{from_date} today))"
    elif to_date:
        return f"(and {query} (between today +{to_date}))"

    return query


@mcp.tool()
def get_personal_notes_instructions() -> str:
    """Get instructions on how to use the get_personal_notes tool.
    
    This will return instructions on how the user organizes their personal notes in Logseq.

    It will contain common tags (topics), what they mean, and the workflows the user
    uses to organize their notes.
    """

    return guide()


@mcp.tool()
def get_personal_notes(topics: list[str], from_date: str = None, to_date: str = None) -> str:
    """Retrieve personal notes from Logseq.

    Use this to find relavant information about a specific topic or about user preferences.
    It will return all information that is tagged with the topics from the user's personal
    knowledge base.

    The information is returned in markdown format, each item in the list is a separate
    unit of information. Hierachical information is returned as a nested list.

    The returning markdown contains text in double square brackets, like this:
    `[[topic]]`. These are links to other topics, you can follow them to get more
    information. Try variations of the topic to find the most relevant information.

    Dates are expressed as:
    1. today|yesterday|tomorrow|now
    2. <number><unit> like 1d, 2w, 3m, 4y, 2h, 30min

    Args:
        topics: A list of topics to search for. Topics are case-insensitive. Topics
                are optional if there is a date range.
        from_date (optional): The start date to filter the notes.
        to_date (optional): The end date to filter the notes.

    Returns:
        A markdown formatted string containing the information with the given topics.
        Empty if no information is found.
    """
    if len(topics) > 0:
        formatted_topics = [f'[[{topic}]]' for topic in topics]
        formatted_topics = " ".join(formatted_topics)
        query = f'(or {formatted_topics})'
        query = date_range_to_query(query, from_date, to_date)
        rslt = req("logseq.DB.q", query)

        # If the topic is not found by tag, try to find via full text search.
        if rslt == "":
            formatted_topics = [f'"{topic}"' for topic in topics]
            formatted_topics = " ".join(formatted_topics)
            query = f'(or {formatted_topics})'
            query = date_range_to_query(query, from_date, to_date)
            rslt = req("logseq.DB.q", query)

        return rslt

    if from_date or to_date:
        query = date_range_to_query(None, from_date, to_date)
        return req("logseq.DB.q", query)

    return guide()

@mcp.tool()
def get_todo_list(done: bool = False, from_date: str = None, to_date: str = None) -> str:
    """Retrieve the todo list from Logseq.

    Use this to get a list of all the todos in the user's personal knowledge base.

    Dates are expressed as:
    1. today|yesterday|tomorrow|now
    2. <number><unit> like 1d, 2w, 3m, 4y, 2h, 30min

    Args:
        done: Whether to get the done todos or the todo todos.
        from_date (optional): The start date to filter the todos.
        to_date (optional): The end date to filter the todos.

    Returns:
        A markdown formatted string containing the todos.
    """
    task = "(task done)" if done else "(task todo)"

    task = date_range_to_query(task, from_date, to_date)

    return req("logseq.DB.q", task)


def req(method: str, *args: list) -> str:
    """Make authenticated request to Logseq API and convert the response to markdown."""
    return page_to_markdown(request(method, *args))