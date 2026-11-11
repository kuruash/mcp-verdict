"""MCP stdio fixture exposing a structured-result tool."""

from typing import Any

from mcp.server.fastmcp import FastMCP

server = FastMCP("mcp-verdict-structured-tool")


@server.tool()
def structured() -> dict[str, Any]:
    """Return nested objects, arrays, and scalar values."""
    return {
        "profile": {"id": 7, "roles": ["admin", "reviewer"]},
        "active": True,
        "values": [1, 2, {"nested": "value"}],
    }


if __name__ == "__main__":
    server.run(transport="stdio")
