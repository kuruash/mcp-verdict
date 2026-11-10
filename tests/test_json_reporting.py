"""Integration tests for structured CLI reports."""

import json
import os
import subprocess
import sys
from pathlib import Path

from mcp_verdict.reporting.json import write_atomic


ROOT = Path(__file__).parents[1]
CLI = Path(sys.executable).parent / "mcp-verdict"


def _run(config: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(CLI), "check", "--config", str(config), "--format", "json", *extra],
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )


def _config(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8")
    return path


def test_json_pass_report_is_one_document(tmp_path: Path) -> None:
    """Serialize a passing check with its observed outcome."""
    server = ROOT / "examples/basic_stdio/server.py"
    config = _config(
        tmp_path / "pass.yaml",
        f"server:\n  command: [{sys.executable}, {server}]\ntool:\n  name: ping\n  arguments: {{}}\nexpected: success\n",
    )

    result = _run(config)
    document = json.loads(result.stdout)

    assert result.returncode == 0
    assert document["schema_version"] == "1"
    assert document["summary"] == {"passed": 1, "failed": 0, "errored": 0}
    assert document["checks"][0]["status"] == "PASS"
    assert document["checks"][0]["actual"] == "success"


def test_json_fail_and_error_reports_preserve_order(tmp_path: Path) -> None:
    """Serialize mismatch and transport errors without inventing outcomes."""
    server = ROOT / "examples/basic_stdio/server.py"
    config = _config(
        tmp_path / "mixed.yaml",
        f"checks:\n"
        f"  - name: mismatch\n    server:\n      command: [{sys.executable}, {server}]\n    tool:\n      name: ping\n      arguments: {{}}\n    expected: tool_error\n"
        "  - name: missing\n    server:\n      command: [missing-mcp-server]\n    tool:\n      name: ping\n      arguments: {}\n    expected: success\n",
    )

    result = _run(config)
    document = json.loads(result.stdout)

    assert result.returncode == 2
    assert [check["name"] for check in document["checks"]] == ["mismatch", "missing"]
    assert document["summary"] == {"passed": 0, "failed": 1, "errored": 1}
    assert document["checks"][0]["status"] == "FAIL"
    assert document["checks"][1]["status"] == "ERROR"
    assert document["checks"][1]["actual"] is None


def test_json_configuration_error_uses_error_envelope(tmp_path: Path) -> None:
    """Return a machine-readable envelope for global configuration errors."""
    config = _config(tmp_path / "invalid.yaml", "expected: unknown\n")

    result = _run(config)
    document = json.loads(result.stdout)

    assert result.returncode == 2
    assert document == {
        "schema_version": "1",
        "error": {"code": "configuration_error", "message": "Check 'check' requires 'server' and 'tool' mappings"},
    }


def test_json_output_file_matches_stdout(tmp_path: Path) -> None:
    """Write the same JSON document to an explicitly requested report file."""
    server = ROOT / "examples/basic_stdio/server.py"
    config = _config(
        tmp_path / "pass.yaml",
        f"server:\n  command: [{sys.executable}, {server}]\ntool:\n  name: ping\n  arguments: {{}}\nexpected: success\n",
    )
    report = tmp_path / "reports" / "report.json"

    result = _run(config, "--output", str(report))

    assert result.returncode == 0
    assert json.loads(report.read_text(encoding="utf-8"))["summary"]["passed"] == 1
    assert result.stdout == ""


def test_json_output_write_failure_is_error(tmp_path: Path) -> None:
    """Report an invalid output target with setup-error exit code."""
    server = ROOT / "examples/basic_stdio/server.py"
    config = _config(
        tmp_path / "pass.yaml",
        f"server:\n  command: [{sys.executable}, {server}]\ntool:\n  name: ping\n  arguments: {{}}\nexpected: success\n",
    )
    output_directory = tmp_path / "existing-directory"
    output_directory.mkdir()

    result = _run(config, "--output", str(output_directory))

    assert result.returncode == 2
    assert "error:" in result.stderr
    assert json.loads(result.stdout)["error"]["code"] == "report_write_error"


def test_json_report_omits_sensitive_tool_arguments(tmp_path: Path) -> None:
    """Do not serialize configured argument values into diagnostic reports."""
    server = ROOT / "examples/basic_stdio/server.py"
    secret = "sk-live-sensitive"
    config = _config(
        tmp_path / "secret.yaml",
        f"server:\n  command: [{sys.executable}, {server}]\n"
        f"tool:\n  name: ping\n  arguments:\n    token: {secret}\n"
        "expected: success\n",
    )

    result = _run(config)

    assert result.returncode == 0
    assert secret not in result.stdout


def test_atomic_writer_cleans_temporary_file_after_replace_failure(
    tmp_path: Path, monkeypatch
) -> None:
    """Remove the temporary report when replacement fails."""
    target = tmp_path / "report.json"

    def fail_replace(source: str, destination: str) -> None:
        raise OSError("simulated replace failure")

    monkeypatch.setattr(os, "replace", fail_replace)

    try:
        write_atomic(target, "{}\n")
    except OSError:
        pass
    else:  # pragma: no cover - defensive assertion
        raise AssertionError("write_atomic should propagate replacement failures")

    assert not target.exists()
    assert list(tmp_path.glob(".report.json.*")) == []
