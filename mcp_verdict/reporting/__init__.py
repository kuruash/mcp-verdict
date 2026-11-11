"""Typed internal results and summaries for MCP Verdict executions."""

from dataclasses import dataclass
from enum import StrEnum

from mcp_verdict.outcomes import ToolOutcome


class CheckStatus(StrEnum):
    """Terminal status of one configured check."""

    PASS = "PASS"
    FAIL = "FAIL"
    ERROR = "ERROR"


class DiagnosticCode(StrEnum):
    """Stable category for safe check diagnostics."""

    OUTCOME_MISMATCH = "outcome_mismatch"
    TOOL_ERROR = "tool_error"
    INITIALIZATION_FAILURE = "initialization_failure"
    TRANSPORT_DISCONNECT = "transport_disconnect"
    TIMEOUT = "timeout"
    CONFIGURATION_ERROR = "configuration_error"
    HTTP_STATUS_MISMATCH = "http_status_mismatch"
    AUTHENTICATION_FAILURE = "authentication_failure"
    AUTHORIZATION_FAILURE = "authorization_failure"


@dataclass(frozen=True)
class CheckResult:
    """Immutable result for one configured check.

    Attributes:
        name: User-facing check name.
        status: PASS, FAIL, or ERROR status.
        expected: Outcome declared by the configuration.
        actual: Observed tool outcome, or ``None`` when execution failed first.
        message: Safe human-readable diagnostic message.
    """

    name: str
    status: CheckStatus
    expected: ToolOutcome
    actual: ToolOutcome | None
    message: str
    diagnostic_code: DiagnosticCode | None = None
    expected_http_status: int | None = None
    actual_http_status: int | None = None


@dataclass(frozen=True)
class ExecutionSummary:
    """Ordered immutable collection of check results and derived totals.

    An empty summary represents zero checks and has exit code zero. Execution
    errors take precedence over outcome mismatches when deriving an exit code.

    Attributes:
        results: Results in the order the checks were executed.
    """

    results: tuple[CheckResult, ...]

    @property
    def passed(self) -> int:
        """Return the number of passing checks."""
        return sum(result.status is CheckStatus.PASS for result in self.results)

    @property
    def failed(self) -> int:
        """Return the number of mismatched checks."""
        return sum(result.status is CheckStatus.FAIL for result in self.results)

    @property
    def errored(self) -> int:
        """Return the number of execution or setup errors."""
        return sum(result.status is CheckStatus.ERROR for result in self.results)

    @property
    def exit_code(self) -> int:
        """Return the CLI exit code represented by this summary."""
        if self.errored:
            return 2
        return 1 if self.failed else 0
