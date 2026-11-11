"""MCP stdio fixture exposing a tool that fails during execution."""

from mcp.server.fastmcp import FastMCP

server = FastMCP("mcp-verdict-error-tool")


@server.tool()
def divide(numerator: int, denominator: int) -> float:
    """Divide two integers and fail when the denominator is zero."""
    return numerator / denominator


if __name__ == "__main__":
    server.run(transport="stdio")
