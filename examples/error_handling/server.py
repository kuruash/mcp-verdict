"""Deliberately incorrect MCP error-reporting example."""

from mcp.server.fastmcp import FastMCP

server = FastMCP("mcp-verdict-incorrect-error-example")


@server.tool()
def known_failure() -> str:
    """Return failure text while incorrectly reporting a successful result."""
    return "known failure"


if __name__ == "__main__":
    server.run(transport="stdio")
