# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
A Model Context Protocol (MCP) server for interacting with Logseq Personal Knowledge Management system using custom instructions, enabling access to Logseq pages and blocks via the MCP interface.

## Commands
- Run tests: `uv run pytest src`
- Run single test: `uv run pytest src/mcp_pkm_logseq/test_file.py::test_function`
- Run tests for a single function: `uv run pytest src/mcp_pkm_logseq/test_file.py -k test_function`
- Install dependencies: `uv sync`
- Build package: `uv build`
- Publish package: `uv publish`

## Coding guideline
- Use Test Driven Development:
    1. Start with single test.
    2. Run the test and make sure it fails.
    3. Implement the code to make the code pass.
    4. Run the test again, if it fails fix the code until the test passes.
    5. After it passes, run all tests. Fix any pending failure.
    6. If everything passes, start again from step 1 with a more complex test.
    7. Repeat until the funcionality is fully implemented.

## Style Guidelines
- Follow Python 3.12+ features and idioms
- Use type hints for all function parameters and return values
- Use dataclasses for data structures
- Docstrings: use triple-quoted docstrings with Args/Returns sections
- Exception handling: use specific exceptions with meaningful error messages
- Naming: snake_case for functions/variables, PascalCase for classes
- Testing: pytest fixtures for test setup, descriptive test names
- Imports: group standard library, third-party, and local imports