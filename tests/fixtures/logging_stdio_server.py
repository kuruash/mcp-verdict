"""MCP stdio fixture that logs diagnostics to stderr."""

import sys

from mcp.server.fastmcp import FastMCP

server = FastMCP("mcp-verdict-logging-test-server")


@server.tool()
def ping() -> str:
    """Return a health-check response."""
    return "pong"


if __name__ == "__main__":
    print("fixture diagnostic: starting MCP server", file=sys.stderr, flush=True)
    server.run(transport="stdio")
