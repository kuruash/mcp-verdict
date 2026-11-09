from mcp.server.fastmcp import FastMCP


server = FastMCP("mcp-verdict-test-server")


@server.tool()
def ping() -> str:
    return "pong"


if __name__ == "__main__":
    server.run(transport="stdio")
