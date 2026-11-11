"""Smoke tests for the public basic stdio server example."""

import sys
from pathlib import Path

import anyio


def test_basic_stdio_example_exposes_ping_and_add() -> None:
    """Connect to the example and discover both documented tools."""
    from mcp_verdict.stdio import connect_to_server

    server_path = Path(__file__).parents[1] / "examples" / "basic_stdio" / "server.py"

    async def discover_tools() -> None:
        async with connect_to_server([sys.executable, str(server_path)]) as connection:
            tools = await connection.session.list_tools()

        tool_names = {tool.name for tool in tools.tools}
        assert {"ping", "add"}.issubset(tool_names)

    anyio.run(discover_tools)
