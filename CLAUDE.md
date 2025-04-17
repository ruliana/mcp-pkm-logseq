# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
A Model Context Protocol (MCP) server for interacting with Logseq Personal Knowledge Management system. This package enables AI assistants to access Logseq pages and blocks through the MCP interface, making personal knowledge available for retrieval during conversations.

The project consists of:
- `server.py`: MCP server with resources and tools definition
- `request.py`: HTTP client handling Logseq API communication
- `to_markdown.py`: Converts Logseq page/block structure to markdown format

## Environment Variables
- `LOGSEQ_API_KEY`: API key for authenticating with Logseq
- `LOGSEQ_URL`: Logseq API endpoint (default: http://localhost:12315)

## Commands
- Run tests: `uv run pytest src`
- Run single test: `uv run pytest src/mcp_pkm_logseq/test_file.py::test_function`
- Run tests for a single function: `uv run pytest src/mcp_pkm_logseq/test_file.py -k test_function`
- Install dependencies: `uv sync`
- Build package: `uv build`
- Publish package: `uv publish`

## Claude Code Task Management
Use these Claude Code slash commands to manage task documentation:
- `/project:new-task "Task Title"` - Create a new task.md with comprehensive context
- `/project:archive-task [optional-component]` - Archive current task.md to the tasks directory
- `/project:use-task-context [search-terms]` - Find relevant context from past tasks
- `/project:list-tasks [optional-component]` - List all archived tasks with filtering

## Project Structure
- `server.py`: Main MCP server with:
  - `guide()`: Resource showing initial instructions
  - `personal_notes()`: Tool retrieving notes by topic tags
- `request.py`: Handles HTTP requests to Logseq API with error handling
- `to_markdown.py`: Data models and conversion logic:
  - `Page` dataclass: Page metadata 
  - `Block` dataclass: Hierarchical block structure
  - `page_to_markdown()`: Main conversion function

## Coding Guidelines
- Use Test Driven Development:
    1. Start with single test.
    2. Run the test and make sure it fails.
    3. Implement the code to make the code pass.
    4. Run the test again, if it fails fix the code until the test passes.
    5. After it passes, run all tests. Fix any pending failure.
    6. If everything passes, start again from step 1 with a more complex test.
    7. Repeat until the functionality is fully implemented.

## Style Guidelines
- Follow Python 3.12+ features and idioms
- Use type hints for all function parameters and return values
- Use dataclasses for data structures
- Docstrings: use triple-quoted docstrings with Args/Returns sections
- Exception handling: use specific exceptions with meaningful error messages
- Naming: snake_case for functions/variables, PascalCase for classes
- Testing: pytest fixtures for test setup, descriptive test names
- Imports: group standard library, third-party, and local imports
- Error handling: Use MCP error framework with appropriate error codes