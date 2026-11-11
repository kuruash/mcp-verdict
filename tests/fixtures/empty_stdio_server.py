"""MCP stdio fixture that exposes no tools."""

from mcp.server.fastmcp import FastMCP

server = FastMCP("mcp-verdict-empty-test-server")


if __name__ == "__main__":
    server.run(transport="stdio")
