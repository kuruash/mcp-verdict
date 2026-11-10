"""Deterministic JSON serialization for MCP Verdict reports."""

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from mcp_verdict.reporting import CheckResult, ExecutionSummary


SCHEMA_VERSION = "1"


def _check_document(result: CheckResult) -> dict[str, Any]:
    """Convert one typed result to JSON-native values."""
    return {
        "name": result.name,
        "status": result.status.value,
        "expected": result.expected.value,
        "actual": result.actual.value if result.actual is not None else None,
        "message": result.message,
        "diagnostic_code": (
            result.diagnostic_code.value if result.diagnostic_code is not None else None
        ),
    }


def summary_document(summary: ExecutionSummary) -> dict[str, Any]:
    """Return the versioned JSON document for an execution summary."""
    return {
        "schema_version": SCHEMA_VERSION,
        "summary": {
            "passed": summary.passed,
            "failed": summary.failed,
            "errored": summary.errored,
        },
        "checks": [_check_document(result) for result in summary.results],
    }


def error_document(code: str, message: str) -> dict[str, Any]:
    """Return a versioned JSON envelope for a global error."""
    return {
        "schema_version": SCHEMA_VERSION,
        "error": {"code": code, "message": message},
    }


def dumps(document: dict[str, Any]) -> str:
    """Serialize a report deterministically as one newline-terminated document."""
    return json.dumps(document, indent=2, sort_keys=True) + "\n"


def write_atomic(path: Path, content: str) -> None:
    """Atomically replace ``path`` with report content.

    Parent directories are created when absent. Existing report files are
    intentionally replaced; callers should choose an explicit output path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
        ) as handle:
            temporary = handle.name
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
