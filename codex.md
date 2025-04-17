# Codex Reference: mcp-pkm-logseq

This document provides a concise reference for the **mcp-pkm-logseq** project: its purpose, core components, tools, coding conventions, and development workflows.

---

## 1. Overview
- **Goal**: Expose your Logseq graph to AI agents via the Model Context Protocol (MCP).
- **Key Features**:
  - `get_personal_notes_instructions()`: Fetches initial guide content.
  - `get_personal_notes(topics, from_date, to_date)`: Retrieves user notes by topic/date.
  - `get_todo_list(done, from_date, to_date)`: Retrieves TODOs or completed tasks by date.

## 2. Core Modules
- **request.py**
  - Authenticates requests using `LOGSEQ_API_TOKEN`/`LOGSEQ_API_KEY` and `LOGSEQ_URL`.
  - `request(method, *args) -> dict`: Makes JSON‐RPC calls; raises `McpError` on failure.
- **to_markdown.py**
  - Models API response as `Page` and `Block` dataclasses.
  - Pipeline functions:
    1. `clean_response`: Build models from raw JSON.
    2. `extract_properties`: Pulls out page‐level properties.
    3. `reorganize_blocks`: Constructs block hierarchy via `parent_id` and `left_id`.
    4. `format_blocks`: Recursively emits Markdown lists (handles code fences and properties).
  - `page_to_markdown(response) -> str`: Facade to generate final Markdown.
- **server.py**
  - Creates `FastMCP` server named **MCP PKM Logseq**.
  - Registers:
    - Resource `logseq://guide` → returns page content as Markdown.
    - Tools: `get_personal_notes_instructions`, `get_personal_notes`, `get_todo_list`.
- **scripts/query_topics**
  - CLI helper to run topic searches and dump raw + Markdown responses (for manual testing).

## 3. Tools & Dependencies
- **Language**: Python ≥ 3.12.
- **Core Dependencies**:
  - `mcp[cli]` (FastMCP)
  - `requests`
  - `pytest`, `pytest-cov`
- **Packaging**:
  - Build with Hatchling (`uv sync`, `uv build`, `uv publish`).
  - Entry point: `mcp_pkm_logseq:main` → CLI script `mcp-pkm-logseq`.

## 4. Coding Style & Conventions
- Follow **PEP 8** (4‐space indent, max line length ~88).
- Use **type hints** and **docstrings** liberally on public APIs.
- Prefer **pure, single‐responsibility** functions.
- Model data with **dataclasses**.
- Place **unit tests** next to modules (`*_test.py`), run via `pytest`.
- Keep external dependencies minimal; favor standard library.

## 5. Development Workflow
1. Enable Logseq HTTP API (Settings → Advanced → HTTP API Server, set token).
2. Export environment variables:
   ```bash
   export LOGSEQ_API_TOKEN=your-token
   export LOGSEQ_URL=http://localhost:12315
   ```
3. Start MCP server:
   ```bash
   mcp-pkm-logseq
   ```
4. Launch the MCP Inspector for live debugging:
   ```bash
   npx @modelcontextprotocol/inspector uv --directory . run mcp-pkm-logseq
   ```
5. Alternatively, invoke tools directly from an AI agent.
6. Run tests:
   ```bash
   pytest src/mcp_pkm_logseq
   ```
7. Build & publish via `uv`:
   ```bash
   uv sync
   uv build
   uv publish
   ```

## 6. Project Layout
```
.
├── src/mcp_pkm_logseq/      # Core library modules
├── scripts/                 # Utility scripts (e.g., query_topics)
├── tasks/                   # Archived development tasks
├── dist/                    # Build artifacts (wheels, sdists)
├── pyproject.toml           # Project metadata & build config
└── codex.md                 # This reference file
```