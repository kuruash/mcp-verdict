"""MCP stdio fixture that exits while executing a tool."""

import os

from mcp.server.fastmcp import FastMCP


server = FastMCP("mcp-verdict-disconnecting-tool")


@server.tool()
def disconnect() -> str:
    """Terminate the server process before returning a result."""
    os._exit(1)


if __name__ == "__main__":
    server.run(transport="stdio")
