"""Local Streamable HTTP MCP fixture for integration tests."""

import sys

import uvicorn
from mcp.server.fastmcp import FastMCP

server = FastMCP("mcp-verdict-http")


@server.tool()
def ping() -> str:
    """Return a deterministic health response."""
    return "pong"


if __name__ == "__main__":
    uvicorn.run(server.streamable_http_app(), host="127.0.0.1", port=int(sys.argv[1]))
