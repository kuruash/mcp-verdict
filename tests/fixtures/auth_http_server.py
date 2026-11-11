"""Local authenticated Streamable HTTP MCP fixture."""

import sys

import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

server = FastMCP("mcp-verdict-auth-http")


@server.tool()
def ping() -> str:
    """Return a deterministic response for authorized callers."""
    return "pong"


class AuthMiddleware(BaseHTTPMiddleware):
    """Enforce deterministic synthetic bearer-token policy."""

    async def dispatch(self, request, call_next):
        authorization = request.headers.get("authorization")
        if authorization is None:
            return Response(status_code=401, headers={"www-authenticate": "Bearer"})
        if authorization == "Bearer invalid-token":
            return Response(status_code=401, headers={"www-authenticate": "Bearer"})
        if authorization == "Bearer limited-token":
            return Response(status_code=403)
        if authorization != "Bearer valid-token":
            return Response(status_code=401, headers={"www-authenticate": "Bearer"})
        return await call_next(request)


if __name__ == "__main__":
    app = AuthMiddleware(server.streamable_http_app())
    uvicorn.run(app, host="127.0.0.1", port=int(sys.argv[1]))
