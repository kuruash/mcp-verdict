"""Unit tests for MCP Verdict's internal reporting model."""

from mcp_verdict.outcomes import ToolOutcome
from mcp_verdict.reporting import (
    CheckResult,
    CheckStatus,
    ExecutionSummary,
)


def test_passing_check_result() -> None:
    """Represent a successful check with matching outcomes."""
    result = CheckResult(
        name="ping",
        status=CheckStatus.PASS,
        expected=ToolOutcome.SUCCESS,
        actual=ToolOutcome.SUCCESS,
        message="Expected and observed success",
    )

    assert result.status is CheckStatus.PASS
    assert result.actual is ToolOutcome.SUCCESS


def test_mismatched_check_result() -> None:
    """Represent an outcome mismatch as FAIL."""
    result = CheckResult(
        name="unexpected-success",
        status=CheckStatus.FAIL,
        expected=ToolOutcome.TOOL_ERROR,
        actual=ToolOutcome.SUCCESS,
        message="Expected tool_error, observed success",
    )

    assert result.status is CheckStatus.FAIL
    assert result.expected is ToolOutcome.TOOL_ERROR


def test_execution_error_has_no_actual_outcome() -> None:
    """Represent setup or transport errors without inventing an outcome."""
    result = CheckResult(
        name="missing-server",
        status=CheckStatus.ERROR,
        expected=ToolOutcome.SUCCESS,
        actual=None,
        message="Could not start MCP server executable",
    )

    assert result.status is CheckStatus.ERROR
    assert result.actual is None


def test_summary_counts_and_exit_precedence() -> None:
    """Count mixed results and give execution errors precedence over mismatches."""
    results = (
        CheckResult("pass", CheckStatus.PASS, ToolOutcome.SUCCESS, ToolOutcome.SUCCESS, "ok"),
        CheckResult("fail", CheckStatus.FAIL, ToolOutcome.TOOL_ERROR, ToolOutcome.SUCCESS, "mismatch"),
        CheckResult("error", CheckStatus.ERROR, ToolOutcome.SUCCESS, None, "transport"),
    )
    summary = ExecutionSummary(results)

    assert summary.results == results
    assert summary.passed == 1
    assert summary.failed == 1
    assert summary.errored == 1
    assert summary.exit_code == 2


def test_failure_without_error_uses_exit_code_one() -> None:
    """Use exit code one when only outcome mismatches exist."""
    summary = ExecutionSummary(
        (CheckResult("fail", CheckStatus.FAIL, ToolOutcome.SUCCESS, ToolOutcome.TOOL_ERROR, "mismatch"),)
    )

    assert summary.exit_code == 1


def test_empty_summary_is_successful() -> None:
    """Define an empty result collection as zero checks and exit code zero."""
    summary = ExecutionSummary(())

    assert summary.passed == 0
    assert summary.failed == 0
    assert summary.errored == 0
    assert summary.exit_code == 0
