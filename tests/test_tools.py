"""Integration tests for MCP tool execution."""

import sys
from pathlib import Path

import anyio
import pytest


def test_executes_ping_tool_successfully() -> None:
    """Invoke ``ping`` through a live MCP session and preserve its result."""
    from mcp_verdict.stdio import connect_to_server
    from mcp_verdict.tools import execute_tool

    server_path = (
        Path(__file__).parents[1] / "examples" / "basic_stdio" / "server.py"
    )

    async def invoke_ping() -> None:
        async with connect_to_server([sys.executable, str(server_path)]) as connection:
            result = await execute_tool(connection.session, "ping")

        assert result.isError is False
        assert result.content[0].text == "pong"

    anyio.run(invoke_ping)


def test_executes_add_tool_with_arguments() -> None:
    """Pass integer arguments to ``add`` and preserve its successful result."""
    from mcp_verdict.stdio import connect_to_server
    from mcp_verdict.tools import execute_tool

    server_path = (
        Path(__file__).parents[1] / "examples" / "basic_stdio" / "server.py"
    )

    async def invoke_add() -> None:
        async with connect_to_server([sys.executable, str(server_path)]) as connection:
            result = await execute_tool(
                connection.session,
                "add",
                arguments={"a": 7, "b": 5},
            )

        assert result.isError is False
        assert result.content[0].text == "12"

    anyio.run(invoke_add)


def test_nonexistent_tool_returns_tool_error_result() -> None:
    """Represent an unknown tool as an MCP error result without masking its data."""
    from mcp_verdict.stdio import connect_to_server
    from mcp_verdict.tools import execute_tool

    server_path = (
        Path(__file__).parents[1] / "examples" / "basic_stdio" / "server.py"
    )

    async def invoke_missing_tool() -> None:
        async with connect_to_server([sys.executable, str(server_path)]) as connection:
            result = await execute_tool(connection.session, "does_not_exist")

        assert result.isError is True
        assert result.content

    anyio.run(invoke_missing_tool)


def test_expected_tool_execution_error_sets_is_error() -> None:
    """Report a tool exception as an MCP tool-level error result."""
    from mcp_verdict.stdio import connect_to_server
    from mcp_verdict.tools import execute_tool

    server_path = Path(__file__).parent / "fixtures" / "error_tool_server.py"

    async def invoke_divide() -> None:
        async with connect_to_server([sys.executable, str(server_path)]) as connection:
            result = await execute_tool(
                connection.session,
                "divide",
                arguments={"numerator": 1, "denominator": 0},
            )

        assert result.isError is True
        assert result.content

    anyio.run(invoke_divide)


def test_outcome_assertion_detects_incorrect_failure_reporting() -> None:
    """Fail an expected tool-error assertion when ``isError`` is false."""
    from mcp_verdict.outcomes import ToolOutcome, assert_tool_outcome
    from mcp_verdict.stdio import connect_to_server
    from mcp_verdict.tools import execute_tool

    server_path = Path(__file__).parent / "fixtures" / "incorrect_error_server.py"

    async def inspect_outcome() -> None:
        async with connect_to_server([sys.executable, str(server_path)]) as connection:
            result = await execute_tool(connection.session, "known_failure")

        verdict = assert_tool_outcome(result, expected=ToolOutcome.TOOL_ERROR)

        assert verdict.passed is False
        assert verdict.expected is ToolOutcome.TOOL_ERROR
        assert verdict.actual is ToolOutcome.SUCCESS

    anyio.run(inspect_outcome)


def test_invalid_tool_arguments_preserve_server_error_result() -> None:
    """Preserve a server's validation result for invalid tool arguments."""
    from mcp_verdict.outcomes import ToolOutcome, assert_tool_outcome
    from mcp_verdict.stdio import connect_to_server
    from mcp_verdict.tools import execute_tool

    server_path = (
        Path(__file__).parents[1] / "examples" / "basic_stdio" / "server.py"
    )

    async def invoke_with_invalid_arguments() -> None:
        async with connect_to_server([sys.executable, str(server_path)]) as connection:
            result = await execute_tool(
                connection.session,
                "add",
                arguments={"a": "not-an-integer", "b": 5},
            )

        verdict = assert_tool_outcome(result, expected=ToolOutcome.TOOL_ERROR)

        assert verdict.passed is True
        assert verdict.actual is ToolOutcome.TOOL_ERROR
        assert result.content

    anyio.run(invoke_with_invalid_arguments)


def test_tool_execution_timeout_is_bounded() -> None:
    """Stop waiting when a tool exceeds its configured execution timeout."""
    from mcp_verdict.stdio import connect_to_server
    from mcp_verdict.tools import execute_tool

    server_path = Path(__file__).parent / "fixtures" / "slow_tool_server.py"

    async def invoke_slow_tool() -> None:
        with anyio.fail_after(3):
            async with connect_to_server([sys.executable, str(server_path)]) as connection:
                with pytest.raises(TimeoutError, match="MCP tool 'slow' timed out"):
                    await execute_tool(connection.session, "slow", timeout=0.2)

    anyio.run(invoke_slow_tool)


def test_disconnect_during_tool_execution_raises_connection_error() -> None:
    """Report a server that exits before returning a tool result."""
    from mcp_verdict.stdio import connect_to_server
    from mcp_verdict.tools import execute_tool

    server_path = Path(__file__).parent / "fixtures" / "disconnecting_tool_server.py"

    async def invoke_disconnecting_tool() -> None:
        with anyio.fail_after(3):
            async with connect_to_server([sys.executable, str(server_path)]) as connection:
                with pytest.raises(ConnectionError, match="MCP connection closed"):
                    await execute_tool(connection.session, "disconnect")

    anyio.run(invoke_disconnecting_tool)


def test_structured_tool_result_is_preserved() -> None:
    """Preserve nested structured content from a successful tool result."""
    from mcp_verdict.stdio import connect_to_server
    from mcp_verdict.tools import execute_tool

    server_path = Path(__file__).parent / "fixtures" / "structured_tool_server.py"

    async def invoke_structured_tool() -> None:
        async with connect_to_server([sys.executable, str(server_path)]) as connection:
            result = await execute_tool(connection.session, "structured")

        assert result.isError is False
        assert result.structuredContent == {
            "profile": {"id": 7, "roles": ["admin", "reviewer"]},
            "active": True,
            "values": [1, 2, {"nested": "value"}],
        }

    anyio.run(invoke_structured_tool)


def test_sequential_tool_calls_reuse_live_session() -> None:
    """Execute multiple calls in one session and preserve each result."""
    from mcp_verdict.stdio import connect_to_server
    from mcp_verdict.tools import execute_tool

    server_path = (
        Path(__file__).parents[1] / "examples" / "basic_stdio" / "server.py"
    )

    async def invoke_sequentially() -> None:
        async with connect_to_server([sys.executable, str(server_path)]) as connection:
            first = await execute_tool(connection.session, "ping")
            second = await execute_tool(
                connection.session,
                "add",
                arguments={"a": 7, "b": 5},
            )
            third = await execute_tool(connection.session, "ping")

        assert first.isError is False
        assert first.content[0].text == "pong"
        assert second.isError is False
        assert second.content[0].text == "12"
        assert third.isError is False
        assert third.content[0].text == "pong"

    anyio.run(invoke_sequentially)
