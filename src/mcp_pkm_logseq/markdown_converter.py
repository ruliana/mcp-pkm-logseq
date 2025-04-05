import re

def page_to_markdown(response: dict) -> str:
    """Convert Logseq response to markdown."""

    def clean_response(response: dict) -> dict:
        """Clean the response from Logseq."""
        page = response[0]["page"]
        blocks = {
            block["id"]: {
                "content": block["content"],
                "parent_id": block["parent"]["id"],
                "left_id": block["left"]["id"],
            }
            for block in response
        }
        return page, blocks

    def build_markdown(page: dict, blocks: dict) -> str:
        """Build the markdown from the page and blocks."""
        # Start with the page title as a level 1 heading
        markdown = f"# {page['originalName']}\n\n"
        
        # First pass: collect properties and regular blocks
        properties = []
        regular_blocks = {}
        
        for block_id, block in blocks.items():
            content = block["content"]
            if re.match(r"^[\w_-]+::.*$", content):
                properties.append(content)
            else:
                regular_blocks[block_id] = block
        
        # Add properties section if any exist
        if len(properties) > 0:
            markdown += "properties:\n"
            for prop in properties:
                markdown += f"- {prop}\n"
            markdown += "\n"
        
        # Second pass: build the block hierarchy
        def build_block_hierarchy(block_id, level=0):
            block = regular_blocks[block_id]
            content = block["content"]
            
            # Handle code blocks
            if "```" in content:
                lines = content.split("\n")
                markdown = f"{'  ' * level}- {lines[0]}\n"
                markdown += f"{'  ' * (level + 1)}{lines[1]}\n"
                markdown += f"{'  ' * (level + 1)}{lines[2]}\n"
                return markdown
            
            # Regular blocks
            markdown = f"{'  ' * level}- {content}\n"
            
            # Find child blocks and sort them by left_id
            child_blocks = []
            for child_id, child_block in regular_blocks.items():
                if child_block["parent_id"] == block_id:
                    child_blocks.append((child_id, child_block))
            
            # Sort child blocks by following the left_id chain
            sorted_children = []
            current_id = block_id  # Start with the parent block
            
            while len(sorted_children) < len(child_blocks):
                found_next = False
                for child_id, child_block in child_blocks:
                    if child_id not in [c[0] for c in sorted_children]:
                        if child_block["left_id"] == current_id:
                            sorted_children.append((child_id, child_block))
                            current_id = child_id
                            found_next = True
                            break
                
                if not found_next:
                    # If we can't find the next block in the chain, add remaining blocks in any order
                    for child_id, child_block in child_blocks:
                        if child_id not in [c[0] for c in sorted_children]:
                            sorted_children.append((child_id, child_block))
                    break
            
            # Add sorted child blocks
            for child_id, _ in sorted_children:
                markdown += build_block_hierarchy(child_id, level + 1)
            
            return markdown
    
        # Start with root blocks (those with parent_id matching page id)
        for block_id, block in regular_blocks.items():
            if block["parent_id"] == page["id"]:
                markdown += build_block_hierarchy(block_id)

        return markdown

    page, blocks = clean_response(response)
    return build_markdown(page, blocks) 