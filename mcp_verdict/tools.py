"""Helpers for executing tools through an initialized MCP session."""

from typing import Any

import anyio
from mcp import ClientSession
from mcp.shared.exceptions import McpError
from mcp.types import CallToolResult


async def execute_tool(
    session: ClientSession,
    name: str,
    arguments: dict[str, Any] | None = None,
    *,
    timeout: float | None = None,
) -> CallToolResult:
    """Execute an MCP tool and return the SDK result unchanged.

    Args:
        session: Live initialized MCP client session.
        name: Name of the tool to execute.
        arguments: Optional JSON-compatible tool arguments.
        timeout: Optional maximum seconds to wait for tool execution.

    Returns:
        The SDK ``CallToolResult``, including its ``isError`` and content fields.

    Raises:
        TimeoutError: If execution exceeds ``timeout`` seconds.
        ConnectionError: If the server closes the MCP connection during execution.
        Exception: If the MCP transport or protocol request fails.
    """
    try:
        if timeout is None:
            return await session.call_tool(name, arguments=arguments)
        with anyio.fail_after(timeout):
            return await session.call_tool(name, arguments=arguments)
    except TimeoutError as exc:
        raise TimeoutError(
            f"MCP tool {name!r} timed out after {timeout} seconds"
        ) from exc
    except McpError as exc:
        if str(exc) != "Connection closed":
            raise
        raise ConnectionError("MCP connection closed during tool execution") from exc
