"""MCP stdio fixture exposing a deliberately slow tool."""

import time

from mcp.server.fastmcp import FastMCP

server = FastMCP("mcp-verdict-slow-tool")


@server.tool()
def slow() -> str:
    """Sleep longer than the short execution timeout used by the test."""
    time.sleep(60)
    return "finished"


if __name__ == "__main__":
    server.run(transport="stdio")
