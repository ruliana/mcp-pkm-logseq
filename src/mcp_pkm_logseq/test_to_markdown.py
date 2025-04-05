import pytest
from .to_markdown import (
    clean_response,
    extract_properties,
    reorganize_blocks,
    format_blocks,
    build_markdown,
    Page,
    Block,
)


@pytest.fixture
def example_response():
    return [
        {
            "content": '```python\nprint("This is code")\n```',
            "format": "markdown",
            "id": 8651,
            "left": {"id": 8650},
            "page": {
                "id": 8644,
                "name": "mcp pkm logseq",
                "originalName": "MCP PKM Logseq",
            },
            "parent": {"id": 8647},
            "pathRefs": [{"id": 8644}],
            "properties": {},
            "uuid": "67f14b2e-40f2-46d4-95e1-94f9a2963cea",
        },
        {
            "content": "Sub-block with code",
            "format": "markdown",
            "id": 8650,
            "left": {"id": 8647},
            "page": {
                "id": 8644,
                "name": "mcp pkm logseq",
                "originalName": "MCP PKM Logseq",
            },
            "parent": {"id": 8647},
            "pathRefs": [{"id": 8644}],
            "properties": {},
            "uuid": "67f14b25-bc9e-48d4-9d37-ec6f59b3c3f9",
        },
        {
            "content": "alias:: mcp_logseq_start\nauthor:: [[Ronie Uliana]]",
            "format": "markdown",
            "id": 8648,
            "left": {"id": 8644},
            "page": {
                "id": 8644,
                "name": "mcp pkm logseq",
                "originalName": "MCP PKM Logseq",
            },
            "parent": {"id": 8644},
            "pathRefs": [{"id": 766}, {"id": 3622}, {"id": 8644}, {"id": 8649}],
            "preBlock?": True,
            "properties": {"alias": ["mcp_logseq_start"], "author": ["Ronie Uliana"]},
            "propertiesOrder": ["alias", "author"],
            "propertiesTextValues": {
                "alias": "mcp_logseq_start",
                "author": "[[Ronie Uliana]]",
            },
            "refs": [{"id": 766}, {"id": 3622}, {"id": 8649}],
            "uuid": "67f14ae4-d069-48c8-9eea-7c02157da245",
        },
        {
            "content": "Testing what else do we have here.",
            "format": "markdown",
            "id": 8647,
            "left": {"id": 8645},
            "page": {
                "id": 8644,
                "name": "mcp pkm logseq",
                "originalName": "MCP PKM Logseq",
            },
            "parent": {"id": 8644},
            "pathRefs": [{"id": 8644}],
            "properties": {},
            "uuid": "67f14aa6-6fe5-429c-b944-31a44b6e6093",
        },
        {
            "content": "This is Ronie's personal and profession Logseq.",
            "format": "markdown",
            "id": 8645,
            "left": {"id": 8648},
            "page": {
                "id": 8644,
                "name": "mcp pkm logseq",
                "originalName": "MCP PKM Logseq",
            },
            "parent": {"id": 8644},
            "pathRefs": [{"id": 8644}],
            "properties": {},
            "uuid": "67f14132-52e7-4353-9c01-df726688ff1d",
        },
    ]

@pytest.fixture
def example_output():
    return """# MCP PKM Logseq

properties:
- alias:: mcp_logseq_start
- author:: [[Ronie Uliana]]

- Testing what else do we have here.
   - Sub-block with code
   - ```python
     print("This is code")
     ```
- This is Ronie's personal and profession Logseq.
"""

def test_clean_response(example_response):
    """Test that clean_response correctly converts the API response into Page and Block objects."""
    page, blocks = clean_response(example_response)

    # Test page object
    assert isinstance(page, Page)
    assert page.id == 8644
    assert page.name == "mcp pkm logseq"
    assert page.original_name == "MCP PKM Logseq"

    # Test blocks dictionary
    assert len(blocks) == 5
    assert all(isinstance(block, Block) for block in blocks.values())

    # Test first block
    block = blocks[8651]
    assert block.id == 8651
    assert block.content == '```python\nprint("This is code")\n```'
    assert block.parent_id == 8647
    assert block.left_id == 8650
    assert block.properties == {}

    # Test block with properties
    block = blocks[8648]
    assert block.id == 8648
    assert block.content == "alias:: mcp_logseq_start\nauthor:: [[Ronie Uliana]]"
    assert block.parent_id == 8644
    assert block.left_id == 8644
    assert block.properties == {"alias": ["mcp_logseq_start"], "author": ["Ronie Uliana"]}


def test_clean_response_empty():
    """Test that clean_response raises an error with empty response."""
    with pytest.raises(IndexError):
        clean_response([])


def test_clean_response_missing_page():
    """Test that clean_response raises an error when page information is missing."""
    invalid_response = [{"content": "test", "id": 1}]
    with pytest.raises(KeyError):
        clean_response(invalid_response)


def test_extract_properties():
    """Test that extract_properties correctly separates properties from regular blocks."""
    # Create test blocks
    blocks = {
        1: Block(id=1, content="Regular content", parent_id=0, left_id=0),
        2: Block(
            id=2,
            content="alias:: test\nauthor:: [[Ronie Uliana]], [[John Doe]]",
            parent_id=0,
            left_id=1,
            properties={"alias": ["test"], "author": ["Ronie Uliana", "John Doe"]},
        ),
        3: Block(id=4, content="Another regular block", parent_id=0, left_id=2),
    }

    properties, remaining_blocks = extract_properties(blocks)

    # Test properties list
    assert len(properties) == 2
    assert "alias:: test" in properties
    assert "author:: Ronie Uliana, John Doe" in properties

    # Test remaining blocks
    assert len(remaining_blocks) == 2
    assert 1 in remaining_blocks
    assert 3 in remaining_blocks
    assert 2 not in remaining_blocks


def test_extract_properties_empty():
    """Test that extract_properties handles empty input correctly."""
    properties, remaining_blocks = extract_properties({})
    assert properties == []
    assert remaining_blocks == {}


def test_extract_properties_no_properties():
    """Test that extract_properties handles blocks without properties correctly."""
    blocks = {
        1: Block(id=1, content="Regular content", parent_id=0, left_id=0),
        2: Block(id=2, content="Another block", parent_id=0, left_id=1),
    }

    properties, remaining_blocks = extract_properties(blocks)
    assert properties == []
    assert remaining_blocks == blocks


def test_reorganize_blocks():
    """Test that reorganize_blocks correctly builds the block hierarchy."""
    # Create test blocks with a simple hierarchy
    blocks = {
        1: Block(id=1, content="Root block", parent_id=0, left_id=0),
        2: Block(id=2, content="Child 1", parent_id=1, left_id=1),
        3: Block(id=3, content="Child 2", parent_id=1, left_id=2),
        4: Block(id=4, content="Grandchild", parent_id=2, left_id=2),
    }

    # Reorganize blocks starting from the root (parent_id=0)
    reorganized = reorganize_blocks(blocks, 0)

    # Test the structure
    assert len(reorganized) == 1  # Only one root block
    root_block = reorganized[0]
    assert root_block.id == 1
    assert root_block.content == "Root block"

    # Test children
    assert len(root_block.children) == 2
    child1, child2 = root_block.children

    assert child1.id == 2
    assert child1.content == "Child 1"
    assert child2.id == 3
    assert child2.content == "Child 2"

    # Test grandchild
    assert len(child1.children) == 1
    grandchild = child1.children[0]
    assert grandchild.id == 4
    assert grandchild.content == "Grandchild"
    assert len(grandchild.children) == 0


def test_reorganize_blocks_empty():
    """Test that reorganize_blocks handles empty input correctly."""
    reorganized = reorganize_blocks({}, 0)
    assert reorganized == []


def test_reorganize_blocks_no_children():
    """Test that reorganize_blocks handles blocks without children correctly."""
    blocks = {
        1: Block(id=1, content="Root block", parent_id=0, left_id=0),
        2: Block(id=2, content="Sibling block", parent_id=0, left_id=1),
    }

    reorganized = reorganize_blocks(blocks, 0)
    assert len(reorganized) == 2
    assert reorganized[0].id == 1
    assert reorganized[1].id == 2
    assert all(len(block.children) == 0 for block in reorganized)


def test_format_blocks():
    """Test that format_blocks correctly formats blocks to markdown."""
    # Create test blocks with a simple hierarchy
    blocks = [
        Block(
            id=1,
            content="Root block",
            parent_id=0,
            left_id=0,
            children=[
                Block(
                    id=2,
                    content="Child 1",
                    parent_id=1,
                    left_id=1,
                    children=[
                        Block(
                            id=4,
                            content="Grandchild",
                            parent_id=2,
                            left_id=2,
                            children=[],
                        )
                    ],
                ),
                Block(id=3, content="Child 2", parent_id=1, left_id=2, children=[]),
            ],
        )
    ]

    expected = """- Root block
  - Child 1
    - Grandchild
  - Child 2
"""

    result = format_blocks(blocks)
    assert result == expected


def test_format_blocks_code():
    """Test that format_blocks correctly formats code blocks."""
    blocks = [
        Block(
            id=1,
            content="```python\nprint('Hello')\n```",
            parent_id=0,
            left_id=0,
            children=[],
        )
    ]

    expected = """- ```python
  print('Hello')
  ```
"""

    result = format_blocks(blocks)
    assert result == expected


def test_format_blocks_empty():
    """Test that format_blocks handles empty input correctly."""
    result = format_blocks([])
    assert result == ""


def test_build_markdown():
    """Test that build_markdown correctly combines page title, properties, and blocks."""
    # Create test page
    page = Page(id=0, name="test-page", original_name="Test Page")

    # Create test blocks
    blocks = {
        1: Block(id=1, content="Root block", parent_id=0, left_id=4),
        2: Block(id=2, content="Child 1", parent_id=1, left_id=1),
        3: Block(id=3, content="Child 2", parent_id=1, left_id=2),
        4: Block(id=4, content="alias:: test\nauthor:: [[Ronie Uliana]]", parent_id=0, left_id=0, properties={"alias": ["test"], "author": ["Ronie Uliana"]}),
    }

    expected = """# Test Page

properties:
- alias:: test
- author:: Ronie Uliana

- Root block
  - Child 1
  - Child 2
"""

    result = build_markdown(page, blocks)
    assert result == expected


def test_build_markdown_no_properties():
    """Test that build_markdown handles pages without properties correctly."""
    page = Page(id=0, name="test-page", original_name="Test Page")
    blocks = {1: Block(id=1, content="Root block", parent_id=0, left_id=0)}

    expected = """# Test Page

- Root block
"""

    result = build_markdown(page, blocks)
    assert result == expected


def test_build_markdown_empty():
    """Test that build_markdown handles empty input correctly."""
    page = Page(id=1, name="test-page", original_name="Test Page")
    result = build_markdown(page, {})
    assert result == "# Test Page\n"


def test_reorganize_blocks_complex_hierarchy():
    """Test that reorganize_blocks handles a complex multi-level hierarchy correctly."""
    # Create test blocks with a complex hierarchy
    blocks = {
        1: Block(id=1, content="Root", parent_id=0, left_id=0),
        2: Block(id=2, content="Child 1", parent_id=1, left_id=1),
        3: Block(id=3, content="Child 2", parent_id=1, left_id=2),
        4: Block(id=4, content="Grandchild 1", parent_id=2, left_id=2),
        5: Block(id=5, content="Grandchild 2", parent_id=2, left_id=4),
        6: Block(id=6, content="Great-grandchild", parent_id=4, left_id=4),
        7: Block(id=7, content="Sibling of Child 2", parent_id=1, left_id=3),
    }

    reorganized = reorganize_blocks(blocks, 0)

    # Test root level
    assert len(reorganized) == 1
    root = reorganized[0]
    assert root.id == 1
    assert root.content == "Root"

    # Test first level children
    assert len(root.children) == 3
    child1, child2, child3 = root.children
    assert child1.id == 2
    assert child2.id == 3
    assert child3.id == 7

    # Test second level (grandchildren)
    assert len(child1.children) == 2
    grandchild1, grandchild2 = child1.children
    assert grandchild1.id == 4
    assert grandchild2.id == 5

    # Test third level (great-grandchild)
    assert len(grandchild1.children) == 1
    great_grandchild = grandchild1.children[0]
    assert great_grandchild.id == 6
    assert len(great_grandchild.children) == 0


def test_reorganize_blocks_disconnected_blocks():
    """Test that reorganize_blocks handles disconnected blocks correctly."""
    blocks = {
        1: Block(id=1, content="Root 1", parent_id=0, left_id=0),
        2: Block(id=2, content="Root 2", parent_id=0, left_id=1),
        3: Block(id=3, content="Child of Root 1", parent_id=1, left_id=1),
        4: Block(id=4, content="Child of Root 2", parent_id=2, left_id=2),
    }

    reorganized = reorganize_blocks(blocks, 0)

    # Test that both root blocks are present
    assert len(reorganized) == 2
    root1, root2 = reorganized
    assert root1.id == 1
    assert root2.id == 2

    # Test children of each root
    assert len(root1.children) == 1
    assert root1.children[0].id == 3

    assert len(root2.children) == 1
    assert root2.children[0].id == 4


def test_reorganize_blocks_orphaned_blocks():
    """Test that reorganize_blocks handles orphaned blocks correctly."""
    blocks = {
        1: Block(id=1, content="Root", parent_id=0, left_id=0),
        2: Block(
            id=2, content="Orphaned Child", parent_id=999, left_id=0
        ),  # Non-existent parent
        3: Block(id=3, content="Valid Child", parent_id=1, left_id=1),
    }

    reorganized = reorganize_blocks(blocks, 0)

    # Test that only the valid root and its child are included
    assert len(reorganized) == 1
    root = reorganized[0]
    assert root.id == 1

    assert len(root.children) == 1
    assert root.children[0].id == 3


def test_reorganize_blocks_cyclic_references():
    """Test that reorganize_blocks handles potential cyclic references gracefully."""
    blocks = {
        1: Block(id=1, content="Root", parent_id=0, left_id=0),
        2: Block(id=2, content="Child 1", parent_id=1, left_id=1),
        3: Block(id=3, content="Child 2", parent_id=1, left_id=2),
        4: Block(id=4, content="Child 3", parent_id=1, left_id=3),
    }

    # Create a cycle by making Child 3's left_id point to itself
    blocks[4].left_id = 4

    reorganized = reorganize_blocks(blocks, 0)

    # Test that the structure is still valid despite the cycle
    assert len(reorganized) == 1
    root = reorganized[0]
    assert root.id == 1

    # The order of children might be affected by the cycle,
    # but we should still have all three children
    assert len(root.children) == 3
    child_ids = {child.id for child in root.children}
    assert child_ids == {2, 3, 4}
