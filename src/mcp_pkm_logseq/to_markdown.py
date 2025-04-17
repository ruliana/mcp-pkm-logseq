from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple, List, Any, Set, Callable, Protocol

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
    # Flag indicating if this block is a page-level property block (preBlock?)
    is_page_property: bool = False
    # List of child blocks
    children: List['Block'] = field(default_factory=list)

# ============================================================================
# Property Handling - Functional Approach
# ============================================================================

def format_property_default(key: str, value: Any) -> str:
    """
    Format a property key-value pair using default Logseq style (key:: value).
    
    Args:
        key: The property key
        value: The property value (can be a list, string, or other type)
        
    Returns:
        Formatted property string in the format "key:: value"
    """
    if isinstance(value, list):
        formatted_value = ", ".join(str(v) for v in value)
    else:
        formatted_value = str(value)
    return f"{key}:: {formatted_value}"

def page_to_markdown(
    response: List[Dict[str, Any]], 
    property_filter: Callable[[Block], bool] = lambda block: block.is_page_property and block.properties,
    format_property: Callable[[str, Any], str] = format_property_default
) -> str:
    """
    Convert a Logseq API response to Markdown.
    
    This is the main entry point for converting Logseq pages to Markdown.
    It acts as a facade for the underlying conversion process.
    
    Args:
        response: The raw response from the Logseq API
        property_filter: Function to determine which blocks to extract properties from
                        (defaults to extracting only page-level properties)
        format_property: Function to format property key-value pairs
                        (defaults to format_property_default)
        
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
        
    Advanced Example with Custom Formatting:
        >>> api_response = get_logseq_page("My Page")
        >>> def custom_format(key, value):
        ...     if isinstance(value, list):
        ...         return f"{key}: [{', '.join(value)}]"
        ...     return f"{key}: {value}"
        >>> markdown = page_to_markdown(api_response, format_property=custom_format)
    """
    if not response:
        return ""

    # Process the response into our data model
    pages, blocks = clean_response(response)
    
    # Define a function to convert a page to markdown
    def convert_page_to_markdown(page: Page, page_blocks: Dict[int, Block]) -> str:
        return build_markdown(page, page_blocks, property_filter, format_property)
    
    # Apply the transformation pipeline
    if len(pages) == 1:
        # If there's only one page, convert it to Markdown
        return convert_page_to_markdown(pages[0], blocks)
    else:
        # If there are multiple pages:
        # 1. Sort pages by id in reverse order (newer pages first)
        sorted_pages = sorted(pages, key=lambda p: p.id, reverse=True)
        
        # 2. For each page, filter blocks and convert to markdown
        results = []
        for page in sorted_pages:
            # Filter blocks for this page (functional filter operation)
            page_blocks = {
                block_id: block for block_id, block in blocks.items() 
                if block.page_id == page.id
            }
            results.append(convert_page_to_markdown(page, page_blocks))
        
        # 3. Join the results
        return "\n\n".join(results)

def create_page_from_block_data(block_data: dict) -> Tuple[int, Page]:
    """
    Create a Page object from a block's page data.
    
    Args:
        block_data: Dictionary containing block data from the Logseq API
        
    Returns:
        A tuple containing:
        - Page ID
        - Page object created from the block data
    """
    page_data = block_data["page"]
    page_id = page_data["id"]
    
    return page_id, Page(
        id=page_id,
        name=page_data["name"],
        original_name=page_data["originalName"]
    )

def create_block_from_data(block_data: dict) -> Tuple[int, Block]:
    """
    Create a Block object from a block data dictionary.
    
    Args:
        block_data: Dictionary containing block data from the Logseq API
        
    Returns:
        A tuple containing:
        - Block ID
        - Block object created from the data
    """
    page_id = block_data["page"]["id"]
    is_page_property = block_data.get("preBlock?", False)
    block_id = block_data["id"]
    
    block = Block(
        id=block_id,
        content=block_data["content"],
        parent_id=block_data["parent"]["id"],
        left_id=block_data["left"]["id"],
        page_id=page_id,
        properties=block_data.get("properties", {}),
        is_page_property=is_page_property
    )
    
    return block_id, block

def track_page_order(response: List[dict]) -> List[int]:
    """
    Track the order of pages as they appear in the response.
    Uses dict as an ordered set to preserve insertion order while eliminating duplicates.
    
    Args:
        response: List of dictionaries from the Logseq API response
        
    Returns:
        List of page IDs in the order they appear in the response
    """
    # Use dict.fromkeys to maintain insertion order while eliminating duplicates
    seen_page_ids = dict.fromkeys(
        block_data["page"]["id"] for block_data in response
    )
    
    return list(seen_page_ids)

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
    
    # Extract pages from response
    pages_dict = {}
    for block_data in response:
        page_id, page = create_page_from_block_data(block_data)
        if page_id not in pages_dict:
            pages_dict[page_id] = page
    
    # Convert each block into a Block object
    blocks = {}
    for block_data in response:
        block_id, block = create_block_from_data(block_data)
        blocks[block_id] = block
    
    # Track page order
    seen_page_ids = track_page_order(response)
    
    # Convert pages dictionary to ordered list
    pages = [pages_dict[page_id] for page_id in seen_page_ids]
    
    return pages, blocks

# ============================================================================
# Property Handling - Functional Approach
# ============================================================================

def extract_properties_func(
    blocks: Dict[int, Block],
    property_filter: Callable[[Block], bool] = lambda block: block.is_page_property and block.properties,
    format_property: Callable[[str, Any], str] = format_property_default,
    remove_extracted: bool = True  # Add a flag to control whether to remove extracted blocks
) -> Tuple[List[str], Dict[int, Block]]:
    """
    Functional approach to extract properties from blocks based on a filter.
    
    Args:
        blocks: Dictionary mapping block IDs to Block objects
        property_filter: Function to determine which blocks to extract properties from
                        (defaults to extracting only page-level properties)
        format_property: Function to format property key-value pairs
                        (defaults to format_property_default)
        remove_extracted: Whether to remove blocks that match the filter from the remaining blocks
                         (defaults to True)
        
    Returns:
        A tuple containing:
        - List of property strings formatted according to the format_property function
        - Dictionary of remaining blocks after filtering
    """
    properties = []
    remaining_blocks = {}
    
    for block_id, block in blocks.items():
        matched = property_filter(block)
        should_remove = False
        
        if matched:
            # Extract and format properties
            if block.properties:
                for key, value in block.properties.items():
                    properties.append(format_property(key, value))
            
            # Determine if this block should be removed from remaining blocks
            if remove_extracted:
                should_remove = True
        
        # Only add to remaining blocks if we shouldn't remove it
        if not should_remove:
            remaining_blocks[block_id] = block
    
    return properties, remaining_blocks

# For backward compatibility
def extract_properties(blocks: Dict[int, Block]) -> Tuple[List[str], Dict[int, Block]]:
    """
    Separate page-level properties from regular blocks in the input dictionary.
    
    Args:
        blocks: Dictionary mapping block IDs to Block objects
        
    Returns:
        A tuple containing:
        - List of property strings in the format "key:: value"
        - Dictionary of remaining blocks that are not page-level properties
    """
    return extract_properties_func(blocks)

def find_direct_children(blocks: Dict[int, Block], parent_id: int) -> List[Block]:
    """
    Find all direct children of a given parent block using functional filtering.
    
    Args:
        blocks: Dictionary mapping block IDs to Block objects
        parent_id: ID of the parent block
        
    Returns:
        List of Block objects that are direct children of the specified parent
    """
    return [block for block in blocks.values() if block.parent_id == parent_id]

def find_first_block(children: List[Block], parent_id: int) -> Optional[Block]:
    """
    Find the first block in a sequence (the one with left_id == parent_id).
    
    Args:
        children: List of blocks to search through
        parent_id: ID of the parent block, which should match left_id of the first block
        
    Returns:
        The first block, or None if not found
    """
    for child in children:
        if child.left_id == parent_id:
            return child
    return None

def chain_blocks(children: List[Block], first_block: Block) -> List[Block]:
    """
    Chain blocks together by following left_id references.
    
    Args:
        children: List of blocks to chain
        first_block: The first block in the chain
        
    Returns:
        Ordered list of blocks
    """
    sorted_children = [first_block]
    current_id = first_block.id
    remaining_children = [child for child in children if child.id != first_block.id]
    
    # Follow the left_id chain to order blocks
    while remaining_children:
        found_next = False
        for i, child in enumerate(remaining_children):
            if child.left_id == current_id:
                sorted_children.append(child)
                current_id = child.id
                remaining_children.pop(i)
                found_next = True
                break
        
        # If chain is broken, add remaining blocks in any order
        if not found_next:
            sorted_children.extend(remaining_children)
            break
    
    return sorted_children

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
    # Step 1: Find direct children of this parent
    children = find_direct_children(blocks, parent_id)
    
    if not children:
        return []
    
    # Step 2: Find the first block in the sequence
    first_block = find_first_block(children, parent_id)
    
    # Step 3: Sort children by following the left_id chain
    if first_block:
        sorted_children = chain_blocks(children, first_block)
    else:
        # If we can't find a proper first block, use original order
        sorted_children = children
    
    # Step 4: Recursively organize children of each block
    for child in sorted_children:
        child.children = reorganize_blocks(blocks, child.id)
    
    return sorted_children

def format_block_properties(
    properties: Dict[str, Any], 
    indent: str, 
    format_property: Callable[[str, Any], str] = format_property_default
) -> Optional[str]:
    """
    Format block properties using a functional approach.
    
    Args:
        properties: Dictionary of property key-value pairs
        indent: Indentation string
        format_property: Function to format property key-value pairs
                        (defaults to format_property_default)
    
    Returns:
        Formatted properties string or None if no properties
    """
    if not properties:
        return None
        
    props_parts = [format_property(key, value) for key, value in properties.items()]
    
    if props_parts:
        return f"{indent}properties: {', '.join(props_parts)}"
    return None

def format_block(
    block: Block, 
    level: int = 0, 
    format_property: Callable[[str, Any], str] = format_property_default
) -> str:
    """
    Format a single block to markdown with proper indentation.
    
    Args:
        block: The block to format
        level: The indentation level (number of spaces)
        format_property: Function to format property key-value pairs
                        (defaults to format_property_default)
        
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
    
    # Add block properties if present
    props_indent = "  " * (level + 1)
    properties_str = format_block_properties(block.properties, props_indent, format_property)
    if properties_str:
        result.append(properties_str)
    
    # Format children
    for child in block.children:
        result.append(format_block(child, level + 1, format_property))
    
    return "\n".join(result)

def format_blocks(
    blocks: List[Block], 
    format_property: Callable[[str, Any], str] = format_property_default
) -> str:
    """
    Format a list of blocks to markdown.
    
    Args:
        blocks: List of Block objects to format
        format_property: Function to format property key-value pairs
                        (defaults to format_property_default)
        
    Returns:
        Formatted markdown string
    """
    if not blocks:
        return ""
    
    # Use functional map to transform blocks to markdown strings
    result = [format_block(block, format_property=format_property) for block in blocks]
    
    return "\n".join(result) + "\n"

def build_markdown(
    page: Page, 
    blocks: Dict[int, Block],
    property_filter: Callable[[Block], bool] = lambda block: block.is_page_property and block.properties,
    format_property: Callable[[str, Any], str] = format_property_default
) -> str:
    """
    Build the final markdown output from a page and its blocks.
    
    Args:
        page: The Page object containing page metadata
        blocks: Dictionary mapping block IDs to Block objects
        property_filter: Function to determine which blocks to extract properties from
                        (defaults to extracting only page-level properties)
        format_property: Function to format property key-value pairs
                        (defaults to format_property_default)
        
    Returns:
        Formatted markdown string with page title, properties, and block hierarchy
    """
    # Pipeline of transformations:
    # 1. Start with the page title
    result = [f"# {page.original_name}", ""]
    
    # 2. Extract and format properties
    properties, remaining_blocks = extract_properties_func(blocks, property_filter, format_property)
    if properties:
        result.append("properties:")
        for prop in properties:
            result.append(f"- {prop}")
        result.append("")
    
    # 3. Reorganize blocks into hierarchical structure
    reorganized_blocks = reorganize_blocks(remaining_blocks, page.id)
    
    # 4. Format blocks to markdown
    block_markdown = format_blocks(reorganized_blocks, format_property)
    if block_markdown:
        result.append(block_markdown)
    
    # 5. Join everything into a single string
    return "\n".join(result) 