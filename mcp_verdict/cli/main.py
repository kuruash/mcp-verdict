"""Argument parsing and command dispatch for MCP Verdict."""

import argparse
from collections.abc import Sequence
from pathlib import Path
import sys

import anyio
from anyio import BrokenResourceError

from mcp_verdict.cli.config import CheckConfig, load_configs
from mcp_verdict.outcomes import assert_tool_outcome
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
        isinstance(leaf, (ConnectionError, OSError, TimeoutError)) for leaf in leaves
    )


def _error_message(error: BaseException) -> str:
    """Return the first useful leaf message from an execution failure."""
    for leaf in _exception_leaves(error):
        if str(leaf):
            return str(leaf)
    return error.__class__.__name__


async def run_check(config: CheckConfig) -> int:
    """Execute one configured check and print its PASS or FAIL verdict."""
    try:
        async with connect_to_server(
            config.command, timeout=config.timeout or 10.0
        ) as connection:
            result = await execute_tool(
                connection.session,
                config.tool_name,
                arguments=config.arguments,
                timeout=config.timeout,
            )
        verdict = assert_tool_outcome(result, expected=config.expected)
        status = "PASS" if verdict.passed else "FAIL"
        print(f"{config.name}: {status}: {verdict.message}")
        return 0 if verdict.passed else 1
    except ExceptionGroup as exc:
        if config.timeout is not None and any(
            isinstance(leaf, BrokenResourceError) for leaf in _exception_leaves(exc)
        ):
            raise TimeoutError(
                f"MCP check timed out after {config.timeout} seconds"
            ) from exc
        raise


async def run_checks(configs: list[CheckConfig]) -> int:
    """Execute checks in order and print a summary of their verdicts."""
    passed = 0
    failed = 0
    errored = 0
    for config in configs:
        try:
            result = await run_check(config)
        except (ConnectionError, OSError, TimeoutError) as exc:
            print(f"error: {config.name}: {exc}", file=sys.stderr)
            errored += 1
            continue
        except Exception as exc:
            if not _is_execution_error(exc):
                raise
            print(f"error: {config.name}: {_error_message(exc)}", file=sys.stderr)
            errored += 1
            continue
        if result == 0:
            passed += 1
        else:
            failed += 1
    print(f"Summary: {passed} passed, {failed} failed, {errored} errored")
    if errored:
        return 2
    return 0 if failed == 0 else 1


def build_parser() -> argparse.ArgumentParser:
    """Build the MCP Verdict argument parser."""
    parser = argparse.ArgumentParser(
        prog="mcp-verdict",
        description="Test MCP server behavior through reproducible checks.",
    )
    commands = parser.add_subparsers(dest="command")
    check = commands.add_parser("check", help="run a configured MCP check")
    check.add_argument("--config", required=True, help="path to a YAML configuration")
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
    try:
        return anyio.run(run_checks, load_configs(Path(args.config)))
    except (ConnectionError, OSError, TimeoutError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
