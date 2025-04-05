from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple, List, Any, Set

@dataclass
class Page:
    """Represents a Logseq page with its metadata."""
    # Unique identifier of the page in the database
    id: int
    # The name used for internal references and queries
    name: str
    # The display name of the page in the UI
    original_name: str

@dataclass
class Block:
    """Represents a Logseq block with its content and relationships."""
    # Unique identifier of the block in the database
    id: int
    # The actual content of the block, including markdown formatting
    content: str
    # ID of the parent block that this block belongs to
    parent_id: int
    # ID of the block that appears before this one in the same level
    left_id: int
    # ID of the page this block belongs to
    page_id: int
    # Optional dictionary containing block properties like aliases, tags, etc.
    properties: Optional[Dict] = None
    # List of child blocks
    children: List['Block'] = field(default_factory=list)
    
def page_to_markdown(response: List[Dict[str, Any]]) -> str:
    """
    Convert a Logseq API response to Markdown.
    
    This is the main entry point for converting Logseq pages to Markdown.
    It acts as a facade for the underlying conversion process.
    
    Args:
        response: The raw response from the Logseq API
        
    Returns:
        A formatted Markdown string representation of the page(s). When multiple
        pages are included in the response, they are sorted by page ID in reverse
        order (larger IDs first), which places newer pages before older ones.
        
    Example:
        >>> api_response = get_logseq_page("My Page")
        >>> markdown = page_to_markdown(api_response)
        >>> print(markdown)
        # My Page
        
        - Block 1
          - Nested block
        - Block 2
    """
    if not response:
        return ""

    # Process the response into our data model
    pages, blocks = clean_response(response)
    
    # If there's only one page, convert it to Markdown
    if len(pages) == 1:
        return build_markdown(pages[0], blocks)
    
    # If there are multiple pages, sort them by id in reverse order (larger ids first),
    # which places newer pages before older ones, then convert each page to Markdown and join them
    results = []
    sorted_pages = sorted(pages, key=lambda p: p.id, reverse=True)
    for page in sorted_pages:
        # Filter blocks for this page
        page_blocks = {
            block_id: block for block_id, block in blocks.items() 
            if block.page_id == page.id
        }
        results.append(build_markdown(page, page_blocks))
    
    return "\n\n".join(results)

def clean_response(response: List[dict]) -> Tuple[List[Page], Dict[int, Block]]:
    """
    Convert the Logseq API response into Page objects and a dictionary of Block objects.
    
    Args:
        response: List of dictionaries from the Logseq API response
        
    Returns:
        A tuple containing:
        - List of Page objects with page metadata
        - Dictionary mapping block IDs to Block objects
        
    Raises:
        IndexError: If the response is empty
        KeyError: If the response is missing required page information
    """
    if not response:
        raise IndexError("Empty response")
    
    # Group blocks by page ID and create Page objects
    pages_dict = {}
    
    for block_data in response:
        page_data = block_data["page"]
        page_id = page_data["id"]
        
        # Create Page object if we haven't seen this page before
        if page_id not in pages_dict:
            pages_dict[page_id] = Page(
                id=page_id,
                name=page_data["name"],
                original_name=page_data["originalName"]
            )
    
    # Convert each block into a Block object
    blocks = {}
    for block_data in response:
        page_id = block_data["page"]["id"]
        block = Block(
            id=block_data["id"],
            content=block_data["content"],
            parent_id=block_data["parent"]["id"],
            left_id=block_data["left"]["id"],
            page_id=page_id,
            properties=block_data.get("properties", {})
        )
        blocks[block.id] = block
    
    # Convert pages dictionary to list, ordered by appearance in response
    seen_page_ids = []
    for block_data in response:
        page_id = block_data["page"]["id"]
        if page_id not in seen_page_ids:
            seen_page_ids.append(page_id)
    
    pages = [pages_dict[page_id] for page_id in seen_page_ids]
    
    return pages, blocks 

def extract_properties(blocks: Dict[int, Block]) -> Tuple[List[str], Dict[int, Block]]:
    """
    Separate properties from regular blocks in the input dictionary.
    
    Args:
        blocks: Dictionary mapping block IDs to Block objects
        
    Returns:
        A tuple containing:
        - List of property strings in the format "key:: value"
        - Dictionary of remaining blocks that are not properties
    """
    properties = []
    remaining_blocks = {}
    
    for block_id, block in blocks.items():
        if block.properties:
            # Convert properties to the format "key:: value"
            for key, values in block.properties.items():
                if isinstance(values, list):
                    value = ", ".join(values)
                else:
                    value = str(values)
                properties.append(f"{key}:: {value}")
        else:
            remaining_blocks[block_id] = block
    
    return properties, remaining_blocks 

def reorganize_blocks(blocks: Dict[int, Block], parent_id: int) -> List[Block]:
    """
    Reorganize blocks into a hierarchical structure based on parent-child relationships.
    
    Args:
        blocks: Dictionary mapping block IDs to Block objects
        parent_id: ID of the parent block to start from
        
    Returns:
        List of Block objects that are direct children of the specified parent,
        with their children recursively organized
    """
    # Find all blocks that are direct children of the parent
    children = []
    for block in blocks.values():
        if block.parent_id == parent_id:
            children.append(block)
    
    if not children:
        return []
    
    # Sort children by following the left_id chain
    sorted_children = []
    current_id = parent_id
    
    # Find the first block (the one with left_id == parent_id)
    for child in children:
        if child.left_id == current_id:
            sorted_children.append(child)
            current_id = child.id
            break
    
    # Sort remaining blocks by following the left_id chain
    while len(sorted_children) < len(children):
        found_next = False
        for child in children:
            if child not in sorted_children and child.left_id == current_id:
                sorted_children.append(child)
                current_id = child.id
                found_next = True
                break
        
        if not found_next:
            # If we can't find the next block in the chain, add remaining blocks in any order
            for child in children:
                if child not in sorted_children:
                    sorted_children.append(child)
            break
    
    # Recursively organize children of each block
    for child in sorted_children:
        child.children = reorganize_blocks(blocks, child.id)
    
    return sorted_children

def format_block(block: Block, level: int = 0) -> str:
    """
    Format a single block to markdown with proper indentation.
    
    Args:
        block: The block to format
        level: The indentation level (number of spaces)
        
    Returns:
        Formatted markdown string for the block and its children
    """
    indent = "  " * level
    result = []
    
    # Handle code blocks
    if "```" in block.content:
        lines = block.content.split("\n")
        result.append(f"{indent}- {lines[0]}")
        for line in lines[1:-1]:
            result.append(f"{indent}  {line}")
        result.append(f"{indent}  {lines[-1]}")
    else:
        result.append(f"{indent}- {block.content}")
    
    # Format children
    for child in block.children:
        result.append(format_block(child, level + 1))
    
    return "\n".join(result)

def format_blocks(blocks: List[Block]) -> str:
    """
    Format a list of blocks to markdown.
    
    Args:
        blocks: List of Block objects to format
        
    Returns:
        Formatted markdown string
    """
    if not blocks:
        return ""
    
    result = []
    for block in blocks:
        result.append(format_block(block))
    
    return "\n".join(result) + "\n"

def build_markdown(page: Page, blocks: Dict[int, Block]) -> str:
    """
    Build the final markdown output from a page and its blocks.
    
    Args:
        page: The Page object containing page metadata
        blocks: Dictionary mapping block IDs to Block objects
        
    Returns:
        Formatted markdown string with page title, properties, and block hierarchy
    """
    # Start with the page title
    result = [f"# {page.original_name}", ""]
    
    # Extract and format properties
    properties, remaining_blocks = extract_properties(blocks)
    if properties:
        result.append("properties:")
        for prop in properties:
            result.append(f"- {prop}")
        result.append("")
    
    # Reorganize and format blocks
    reorganized_blocks = reorganize_blocks(remaining_blocks, page.id)
    block_markdown = format_blocks(reorganized_blocks)
    if block_markdown:
        result.append(block_markdown)
    
    return "\n".join(result) 