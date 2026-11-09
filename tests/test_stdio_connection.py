"""Integration tests for MCP stdio connections."""

import sys
from pathlib import Path

import anyio
import pytest


def test_connects_to_stdio_server_and_initializes_session() -> None:
    """Connect to the fixture and initialize an MCP session."""
    from mcp_verdict.stdio import connect_to_server

    server_path = Path(__file__).parent / "fixtures" / "stdio_server.py"

    async def initialize_session() -> None:
        async with connect_to_server([sys.executable, str(server_path)]) as connection:
            assert connection.initialize_result.protocolVersion

    anyio.run(initialize_session)


def test_discovers_ping_tool_through_live_stdio_session() -> None:
    """Discover the fixture's ``ping`` tool through a live MCP session."""
    from mcp_verdict.stdio import connect_to_server

    server_path = Path(__file__).parent / "fixtures" / "stdio_server.py"

    async def discover_tools() -> None:
        async with connect_to_server([sys.executable, str(server_path)]) as connection:
            tools = await connection.session.list_tools()

        assert any(tool.name == "ping" for tool in tools.tools)

    anyio.run(discover_tools)


def test_initializes_empty_stdio_server_and_discovers_no_tools() -> None:
    """Initialize a server with no tools and verify its empty tool list."""
    from mcp_verdict.stdio import connect_to_server

    server_path = Path(__file__).parent / "fixtures" / "empty_stdio_server.py"

    async def discover_tools() -> None:
        async with connect_to_server([sys.executable, str(server_path)]) as connection:
            assert connection.initialize_result.protocolVersion
            tools = await connection.session.list_tools()

        assert tools.tools == []

    anyio.run(discover_tools)


def test_missing_stdio_executable_raises_connection_error() -> None:
    """Reject a missing server executable without hanging or yielding a session."""
    from mcp_verdict.stdio import connect_to_server

    async def attempt_connection() -> None:
        with anyio.fail_after(5):
            async with connect_to_server(["mcp-verdict-command-that-does-not-exist"]):
                pytest.fail("a missing executable must not yield a session")

    with pytest.raises(ConnectionError, match="Could not start MCP server"):
        anyio.run(attempt_connection)


def test_unexpected_server_exit_during_initialization_raises_connection_error() -> None:
    """Report a server that exits before completing the MCP handshake."""
    from mcp_verdict.stdio import connect_to_server

    server_path = Path(__file__).parent / "fixtures" / "exiting_stdio_server.py"

    async def attempt_connection() -> None:
        with anyio.fail_after(5):
            async with connect_to_server([sys.executable, str(server_path)]):
                pytest.fail("an exited server must not yield a session")

    with pytest.raises(ConnectionError, match="MCP server exited during initialization"):
        anyio.run(attempt_connection)


def test_unresponsive_server_times_out_during_initialization() -> None:
    """Bound initialization time when an MCP server never responds."""
    from mcp_verdict.stdio import connect_to_server

    server_path = Path(__file__).parent / "fixtures" / "unresponsive_stdio_server.py"

    async def attempt_connection() -> None:
        with anyio.fail_after(3):
            async with connect_to_server(
                [sys.executable, str(server_path)], timeout=0.2
            ):
                pytest.fail("an unresponsive server must not yield a session")

    with pytest.raises(TimeoutError, match="MCP server initialization timed out"):
        anyio.run(attempt_connection)


def test_stderr_logging_does_not_corrupt_stdio_protocol() -> None:
    """Initialize and discover tools when the server logs diagnostics to stderr."""
    from mcp_verdict.stdio import connect_to_server

    server_path = Path(__file__).parent / "fixtures" / "logging_stdio_server.py"

    async def discover_tools() -> None:
        async with connect_to_server([sys.executable, str(server_path)]) as connection:
            assert connection.initialize_result.protocolVersion
            tools = await connection.session.list_tools()

        assert any(tool.name == "ping" for tool in tools.tools)

    anyio.run(discover_tools)
