import pytest
from .markdown_converter import page_to_markdown

@pytest.fixture
def example_response():
    return [
        {
            'content': '```python\nprint("This is code")\n```',
            'format': 'markdown',
            'id': 8651,
            'left': {'id': 8650},
            'page': {
                'id': 8644,
                'name': 'mcp pkm logseq',
                'originalName': 'MCP PKM Logseq'
            },
            'parent': {'id': 8647},
            'pathRefs': [{'id': 8644}],
            'properties': {},
            'uuid': '67f14b2e-40f2-46d4-95e1-94f9a2963cea'
        },
        {
            'content': 'Sub-block with code',
            'format': 'markdown',
            'id': 8650,
            'left': {'id': 8647},
            'page': {
                'id': 8644,
                'name': 'mcp pkm logseq',
                'originalName': 'MCP PKM Logseq'
            },
            'parent': {'id': 8647},
            'pathRefs': [{'id': 8644}],
            'properties': {},
            'uuid': '67f14b25-bc9e-48d4-9d37-ec6f59b3c3f9'
        },
        {
            'content': 'alias:: mcp_logseq_start',
            'format': 'markdown',
            'id': 8648,
            'left': {'id': 8644},
            'page': {
                'id': 8644,
                'name': 'mcp pkm logseq',
                'originalName': 'MCP PKM Logseq'
            },
            'parent': {'id': 8644},
            'pathRefs': [{'id': 8644}, {'id': 8649}],
            'preBlock?': True,
            'properties': {'alias': ['mcp_logseq_start']},
            'propertiesOrder': ['alias'],
            'propertiesTextValues': {'alias': 'mcp_logseq_start'},
            'refs': [{'id': 8649}],
            'uuid': '67f14ae4-d069-48c8-9eea-7c02157da245'
        },
        {
            'content': 'Testing what else do we have here.',
            'format': 'markdown',
            'id': 8647,
            'left': {'id': 8645},
            'page': {
                'id': 8644,
                'name': 'mcp pkm logseq',
                'originalName': 'MCP PKM Logseq'
            },
            'parent': {'id': 8644},
            'pathRefs': [{'id': 8644}],
            'properties': {},
            'uuid': '67f14aa6-6fe5-429c-b944-31a44b6e6093'
        },
        {
            'content': "This is Ronie's personal and profession Logseq.",
            'format': 'markdown',
            'id': 8645,
            'left': {'id': 8648},
            'page': {
                'id': 8644,
                'name': 'mcp pkm logseq',
                'originalName': 'MCP PKM Logseq'
            },
            'parent': {'id': 8644},
            'pathRefs': [{'id': 8644}],
            'properties': {},
            'uuid': '67f14132-52e7-4353-9c01-df726688ff1d'
        }
    ]

@pytest.fixture
def expected_markdown():
    return """# MCP PKM Logseq

properties:
- alias:: mcp_logseq_start

- Testing what else do we have here.
  - Sub-block with code
  - ```python
    print("This is code")
    ```
- This is Ronie's personal and profession Logseq.
"""

def test_page_to_markdown(example_response, expected_markdown):
    """Test the page_to_markdown function with example data."""
    result = page_to_markdown(example_response)
    assert result == expected_markdown

def test_empty_response():
    """Test the page_to_markdown function with empty response."""
    with pytest.raises(IndexError):
        page_to_markdown([])

def test_missing_page_info():
    """Test the page_to_markdown function with missing page information."""
    invalid_response = [{'content': 'test', 'id': 1}]
    with pytest.raises(KeyError):
        page_to_markdown(invalid_response) 