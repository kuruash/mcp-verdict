"""Local Streamable HTTP MCP server with deterministic synthetic auth policy."""

import os
import sys

import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


server = FastMCP("mcp-verdict-http-security")


@server.tool()
def ping() -> str:
    """Return a response to authorized callers."""
    return "pong"


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Require the synthetic token configured for this local example."""

    async def dispatch(self, request, call_next):
        authorization = request.headers.get("authorization")
        expected = os.environ.get("MCP_VERDICT_EXAMPLE_TOKEN", "valid-token")
        if authorization is None:
            return Response(status_code=401, headers={"www-authenticate": "Bearer"})
        if authorization == "Bearer invalid-token":
            return Response(status_code=401, headers={"www-authenticate": "Bearer"})
        if authorization == "Bearer limited-token":
            return Response(status_code=403)
        if authorization != f"Bearer {expected}":
            return Response(status_code=401, headers={"www-authenticate": "Bearer"})
        return await call_next(request)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    uvicorn.run(AuthenticationMiddleware(server.streamable_http_app()), host="127.0.0.1", port=port)
