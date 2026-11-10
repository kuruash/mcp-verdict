"""Subprocess integration tests for the public MCP Verdict examples."""

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parents[1]
CLI = Path(sys.executable).parent / "mcp-verdict"


def run_example(example: str, *, expected_exit: int) -> subprocess.CompletedProcess[str]:
    """Run one example configuration from the repository root."""
    config = ROOT / "examples" / example / "verdict.yaml"
    environment = os.environ.copy()
    environment["PATH"] = f"{Path(sys.executable).parent}{os.pathsep}{environment['PATH']}"
    result = subprocess.run(
        [str(CLI), "check", "--config", str(config)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
        env=environment,
    )
    assert result.returncode == expected_exit
    return result


def test_basic_stdio_example_passes() -> None:
    """Run the basic example's successful ping and add checks."""
    result = run_example("basic_stdio", expected_exit=0)

    assert "ping-success: PASS" in result.stdout
    assert "add-success: PASS" in result.stdout
    assert "Summary: 2 passed, 0 failed" in result.stdout


def test_calculator_example_passes_success_and_error_checks() -> None:
    """Run calculator success and expected-error scenarios."""
    result = run_example("calculator", expected_exit=0)

    assert "add: PASS" in result.stdout
    assert "divide: PASS" in result.stdout
    assert "divide-by-zero: PASS" in result.stdout
    assert "Summary: 3 passed, 0 failed" in result.stdout


def test_error_handling_example_reports_intentional_failure() -> None:
    """Detect the server's incorrect success flag for a known failure."""
    result = run_example("error_handling", expected_exit=1)

    assert "known-failure: FAIL" in result.stdout
    assert "Expected tool_error, observed success" in result.stdout
    assert "Summary: 0 passed, 1 failed" in result.stdout
