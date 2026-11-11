"""Argument parsing and command dispatch for MCP Verdict."""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

import anyio
import httpx
from anyio import BrokenResourceError
from mcp.client.streamable_http import StreamableHTTPError
from mcp.shared.exceptions import McpError

from mcp_verdict.cli.config import CheckConfig, load_configs
from mcp_verdict.http import connect_to_http_server, probe_http_status
from mcp_verdict.outcomes import assert_tool_outcome
from mcp_verdict.reporting import (
    CheckResult,
    CheckStatus,
    DiagnosticCode,
    ExecutionSummary,
)
from mcp_verdict.reporting.diagnostics import safe_message
from mcp_verdict.reporting.json import dumps, error_document, summary_document, write_atomic
from mcp_verdict.stdio import connect_to_server
from mcp_verdict.tools import execute_tool


def _exception_leaves(error: BaseException):
    """Yield leaf exceptions from runtimes that wrap failures in groups."""
    children = getattr(error, "exceptions", None)
    if children is None:
        yield error
        return
    for child in children:
        yield from _exception_leaves(child)


def _is_execution_error(error: BaseException) -> bool:
    """Return whether every leaf is a known setup or transport failure."""
    leaves = list(_exception_leaves(error))
    return bool(leaves) and all(
        isinstance(
            leaf,
            (
                ConnectionError,
                OSError,
                TimeoutError,
                httpx.HTTPError,
                McpError,
                StreamableHTTPError,
            ),
        )
        for leaf in leaves
    )


def _error_message(error: BaseException) -> str:
    """Return the first useful leaf message from an execution failure."""
    for leaf in _exception_leaves(error):
        if str(leaf):
            return str(leaf)
    if isinstance(error, ExceptionGroup):
        return "MCP transport returned an invalid or incomplete response"
    return error.__class__.__name__


def _diagnostic_code(error: BaseException) -> DiagnosticCode:
    """Map a known execution exception to a stable diagnostic category."""
    if isinstance(error, TimeoutError):
        return DiagnosticCode.TIMEOUT
    message = _error_message(error).lower()
    if "tool execution" in message or "during tool" in message:
        return DiagnosticCode.TRANSPORT_DISCONNECT
    return DiagnosticCode.INITIALIZATION_FAILURE


async def run_check(config: CheckConfig) -> CheckResult:
    """Execute one configured check and return its typed result."""
    try:
        if config.expected_http_status is not None:
            if config.url is None:
                raise ValueError("HTTP status checks require server.url")
            actual_status = await probe_http_status(
                config.url, timeout=config.timeout or 10.0, auth_env=config.auth_env
            )
            passed = actual_status == config.expected_http_status
            return CheckResult(
                name=config.name,
                status=CheckStatus.PASS if passed else CheckStatus.FAIL,
                expected=config.expected,
                actual=None,
                message=(
                    f"Expected HTTP {config.expected_http_status}, observed HTTP {actual_status}"
                ),
                diagnostic_code=(None if passed else DiagnosticCode.HTTP_STATUS_MISMATCH),
                expected_http_status=config.expected_http_status,
                actual_http_status=actual_status,
            )
        connector = (
            connect_to_http_server(
                config.url,
                timeout=config.timeout or 10.0,
                auth_env=config.auth_env,
            )
            if config.transport == "streamable_http" and config.url is not None
            else connect_to_server(config.command, timeout=config.timeout or 10.0)
        )
        async with connector as connection:
            result = await execute_tool(
                connection.session,
                config.tool_name,
                arguments=config.arguments,
                timeout=config.timeout,
            )
        verdict = assert_tool_outcome(result, expected=config.expected)
        return CheckResult(
            name=config.name,
            status=CheckStatus.PASS if verdict.passed else CheckStatus.FAIL,
            expected=verdict.expected,
            actual=verdict.actual,
            message=verdict.message,
            diagnostic_code=(
                DiagnosticCode.OUTCOME_MISMATCH
                if not verdict.passed
                else (DiagnosticCode.TOOL_ERROR if verdict.actual.value == "tool_error" else None)
            ),
        )
    except ExceptionGroup as exc:
        if config.timeout is not None and any(
            isinstance(leaf, BrokenResourceError) for leaf in _exception_leaves(exc)
        ):
            raise TimeoutError(f"MCP check timed out after {config.timeout} seconds") from exc
        raise


async def run_checks(configs: list[CheckConfig]) -> ExecutionSummary:
    """Execute checks in order and return their typed summary."""
    results: list[CheckResult] = []
    for config in configs:
        try:
            result = await run_check(config)
        except (ConnectionError, OSError, TimeoutError, httpx.HTTPError) as exc:
            result = CheckResult(
                name=config.name,
                status=CheckStatus.ERROR,
                expected=config.expected,
                actual=None,
                message=safe_message(str(exc)),
                diagnostic_code=_diagnostic_code(exc),
            )
        except Exception as exc:
            if not _is_execution_error(exc):
                raise
            result = CheckResult(
                name=config.name,
                status=CheckStatus.ERROR,
                expected=config.expected,
                actual=None,
                message=safe_message(_error_message(exc)),
                diagnostic_code=DiagnosticCode.TRANSPORT_DISCONNECT,
            )
        results.append(result)

    summary = ExecutionSummary(tuple(results))
    return summary


def build_parser() -> argparse.ArgumentParser:
    """Build the MCP Verdict argument parser."""
    parser = argparse.ArgumentParser(
        prog="mcp-verdict",
        description="Test MCP server behavior through reproducible checks.",
    )
    commands = parser.add_subparsers(dest="command")
    check = commands.add_parser("check", help="run a configured MCP check")
    check.add_argument("--config", required=True, help="path to a YAML configuration")
    check.add_argument("--format", choices=("human", "json"), default="human", help="report format")
    check.add_argument("--output", help="write a JSON report to this path")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Parse command-line arguments and return a process exit code.

    Args:
        argv: Optional argument sequence; defaults to ``sys.argv`` when omitted.

    Returns:
        The command's process exit code.
    """
    args = build_parser().parse_args(argv)
    if args.command != "check":
        return 0
    if args.output and args.format != "json":
        print("error: --output requires --format json", file=sys.stderr)
        return 2
    try:
        summary = anyio.run(run_checks, load_configs(Path(args.config)))
    except (ConnectionError, OSError, TimeoutError, ValueError, httpx.HTTPError) as exc:
        message = safe_message(str(exc))
        if args.format == "json":
            content = dumps(error_document("configuration_error", message))
            if args.output:
                try:
                    write_atomic(Path(args.output), content)
                except OSError as write_exc:
                    write_message = f"could not write report: {safe_message(str(write_exc))}"
                    print(f"error: {write_message}", file=sys.stderr)
                    print(
                        dumps(error_document("report_write_error", write_message)),
                        end="",
                    )
            else:
                print(content, end="")
        else:
            print(f"error: {message}", file=sys.stderr)
        return 2
    if args.format == "human":
        for result in summary.results:
            if result.status is CheckStatus.ERROR:
                print(f"error: {result.name}: {result.message}", file=sys.stderr)
            else:
                print(f"{result.name}: {result.status.value}: {result.message}")
        print(
            f"Summary: {summary.passed} passed, {summary.failed} failed, {summary.errored} errored"
        )
        return summary.exit_code
    content = dumps(summary_document(summary))
    if args.output:
        try:
            write_atomic(Path(args.output), content)
        except OSError as exc:
            message = f"could not write report: {safe_message(str(exc))}"
            print(f"error: {message}", file=sys.stderr)
            print(dumps(error_document("report_write_error", message)), end="")
            return 2
    else:
        print(content, end="")
    return summary.exit_code
