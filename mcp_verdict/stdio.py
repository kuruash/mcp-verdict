"""Async connections to MCP servers launched over standard input and output."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

import anyio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.shared.exceptions import McpError
from mcp.types import InitializeResult


@dataclass(frozen=True)
class StdioConnection:
    """Initialized MCP session and the result negotiated during initialization.

    Attributes:
        session: Live MCP client session for requests within the context.
        initialize_result: Server initialization response, including protocol version.
    """

    session: ClientSession
    initialize_result: InitializeResult


@asynccontextmanager
async def connect_to_server(
    command: list[str], *, timeout: float = 10.0
) -> AsyncIterator[StdioConnection]:
    """Connect to and initialize an MCP server over stdio.

    Args:
        command: Executable and arguments used to launch the MCP server.
        timeout: Maximum seconds allowed for MCP initialization.

    Yields:
        An initialized live session and its negotiated initialization result.

    Raises:
        ConnectionError: If the server executable cannot be started or exits during
            initialization.
        TimeoutError: If MCP initialization exceeds ``timeout`` seconds.
        Exception: If MCP initialization or another SDK operation fails.
    """
    server = StdioServerParameters(command=command[0], args=command[1:])

    try:
        try:
            initialized = False
            async with stdio_client(server) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    with anyio.fail_after(timeout):
                        initialize_result = await session.initialize()
                    initialized = True
                    yield StdioConnection(
                        session=session,
                        initialize_result=initialize_result,
                    )
        except* TimeoutError as exc_group:
            if initialized:
                raise
            raise TimeoutError(
                f"MCP server initialization timed out after {timeout} seconds"
            ) from exc_group
        except* McpError as exc_group:
            if initialized:
                raise
            raise ConnectionError(
                "MCP server exited during initialization"
            ) from exc_group
    except FileNotFoundError as exc:
        raise ConnectionError(
            f"Could not start MCP server executable: {command[0]!r}"
        ) from exc
