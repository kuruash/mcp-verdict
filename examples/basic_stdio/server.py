"""Basic MCP stdio server exposing small arithmetic tools."""

from mcp.server.fastmcp import FastMCP


server = FastMCP("mcp-verdict-basic-stdio")


@server.tool()
def ping() -> str:
    """Return a simple health-check response."""
    return "pong"


@server.tool()
def add(a: int, b: int) -> int:
    """Add two integers.

    Args:
        a: First integer.
        b: Second integer.

    Returns:
        The sum of ``a`` and ``b``.
    """
    return a + b


if __name__ == "__main__":
    server.run(transport="stdio")
