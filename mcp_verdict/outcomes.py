"""Explicit outcome classification for MCP tool results."""

from dataclasses import dataclass
from enum import StrEnum

from mcp.types import CallToolResult


class ToolOutcome(StrEnum):
    """Expected or observed protocol-level outcome of a tool call."""

    SUCCESS = "success"
    TOOL_ERROR = "tool_error"


@dataclass(frozen=True)
class OutcomeVerdict:
    """Comparison between a declared and observed tool outcome.

    Attributes:
        passed: Whether the observed outcome matches the expectation.
        expected: Declared outcome.
        actual: Outcome derived from the MCP ``isError`` field.
        result: Original SDK result for further inspection.
    """

    passed: bool
    expected: ToolOutcome
    actual: ToolOutcome
    result: CallToolResult

    @property
    def message(self) -> str:
        """Return a concise explanation of the outcome comparison."""
        if self.passed:
            return f"Expected and observed {self.actual.value}"
        return f"Expected {self.expected.value}, observed {self.actual.value}"


def assert_tool_outcome(result: CallToolResult, *, expected: ToolOutcome) -> OutcomeVerdict:
    """Compare a declared outcome with the MCP result's explicit error flag.

    Args:
        result: Unmodified result returned by the MCP SDK.
        expected: Developer-declared expected outcome.

    Returns:
        A verdict containing the expected and observed outcomes and original result.
    """
    actual = ToolOutcome.TOOL_ERROR if result.isError else ToolOutcome.SUCCESS
    return OutcomeVerdict(
        passed=actual is expected,
        expected=expected,
        actual=actual,
        result=result,
    )
