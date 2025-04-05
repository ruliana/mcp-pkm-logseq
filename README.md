# mcp-pkm-logseq MCP server

A MCP server for interacting with your Logseq Personal Knowledge Management system using custom instructions

## Components

### Resources

- `logseq://start` - Initial instructions on how to interact with this knowledge base
- `logseq://page/{name}` - Get a page from Logseq by name

### Tools

- `get_tagged_blocks(*tags)` - Get all blocks with specified tags or page references


## Configuration

The following environment variables can be configured:

- `LOGSEQ_API_KEY`: API key for authenticating with Logseq (default: "this-is-my-logseq-mcp-token")
- `LOGSEQ_URL`: URL where the Logseq HTTP API is running (default: "http://localhost:12315")

## Quickstart

### Install

#### Claude Desktop

On MacOS: `~/Library/Application\ Support/Claude/claude_desktop_config.json`
On Windows: `%APPDATA%/Claude/claude_desktop_config.json`


<details>
  <summary>Published Servers Configuration</summary>

  ```json
  "mcpServers": {
    "mcp-pkm-logseq": {
      "command": "uvx",
      "args": [
        "mcp-pkm-logseq"
      ],
      "env": {
        "LOGSEQ_API_KEY": "your-logseq-api-token",
        "LOGSEQ_URL": "http://localhost:12315"
      }
    }
  }
  ```
</details>

### Start Logseq server

Logseq's HTTP API is an interface that runs within your desktop Logseq application. When enabled, it starts a local HTTP server (default port 12315) that allows programmatic access to your Logseq knowledge base. The API supports querying pages and blocks, searching content, and potentially modifying content through authenticated requests.

To enable the Logseq HTTP API server:

1. Open Logseq and go to Settings (upper right corner)
2. Navigate to Advanced
3. Enable "Developer mode"
4. Enable "HTTP API Server"
5. Set your API token (this should match the `LOGSEQ_API_KEY` value in the MCP server configuration)

For more detailed instructions, see: https://logseq-copilot.eindex.me/doc/setup

## Development

### Building and Publishing

To prepare the package for distribution:

1. Sync dependencies and update lockfile:
```bash
uv sync
```

2. Build package distributions:
```bash
uv build
```

This will create source and wheel distributions in the `dist/` directory.

3. Publish to PyPI:
```bash
uv publish
```

Note: You'll need to set PyPI credentials via environment variables or command flags:
- Token: `--token` or `UV_PUBLISH_TOKEN`
- Or username/password: `--username`/`UV_PUBLISH_USERNAME` and `--password`/`UV_PUBLISH_PASSWORD`

### Debugging

Since MCP servers run over stdio, debugging can be challenging. For the best debugging
experience, we strongly recommend using the [MCP Inspector](https://github.com/modelcontextprotocol/inspector).


You can launch the MCP Inspector via [`npm`](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm) with this command:

```bash
npx @modelcontextprotocol/inspector uv --directory /Users/ronie/MCP/mcp-pkm-logseq run mcp-pkm-logseq
```


Upon launching, the Inspector will display a URL that you can access in your browser to begin debugging.


### Add Development Servers Configuration to Claude Desktop
```json
"mcpServers": {
  "mcp-pkm-logseq": {
    "command": "uv",
    "args": [
      "--directory",
      "/<parent-directories>/mcp-pkm-logseq",
      "run",
      "mcp-pkm-logseq"
    ],
    "env": {
      "LOGSEQ_API_KEY": "your-logseq-api-token",
      "LOGSEQ_URL": "http://localhost:12315"
    }
  }
}
```