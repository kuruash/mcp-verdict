"""MCP stdio fixture that misreports a known failure as successful."""

from mcp.server.fastmcp import FastMCP

server = FastMCP("mcp-verdict-incorrect-error")


@server.tool()
def known_failure() -> str:
    """Return failure text without setting the MCP error flag."""
    return "known failure"


if __name__ == "__main__":
    server.run(transport="stdio")
