"""Subprocess integration tests for the MCP Verdict command-line interface."""

import subprocess
import sys
from pathlib import Path

import pytest


def test_mcp_verdict_help() -> None:
    """Show usage information from the installed console script."""
    cli_path = Path(sys.executable).parent / "mcp-verdict"
    assert cli_path.exists(), f"CLI is not installed at {cli_path}"

    result = subprocess.run(
        [str(cli_path), "--help"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "usage:" in result.stdout.lower()
    assert "check" in result.stdout


def test_check_runs_configured_ping_tool(tmp_path: Path) -> None:
    """Run a configured stdio check and report PASS for a successful tool."""
    cli_path = Path(sys.executable).parent / "mcp-verdict"
    server_path = Path(__file__).parents[1] / "examples" / "basic_stdio" / "server.py"
    config_path = tmp_path / "ping.yaml"
    config_path.write_text(
        "\n".join(
            [
                "server:",
                "  command:",
                f"    - {sys.executable}",
                f"    - {server_path}",
                "tool:",
                "  name: ping",
                "  arguments: {}",
                "expected: success",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [str(cli_path), "check", "--config", str(config_path)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "PASS" in result.stdout


def test_check_passes_for_expected_tool_error(tmp_path: Path) -> None:
    """Return PASS when a real tool reports the declared tool error outcome."""
    cli_path = Path(sys.executable).parent / "mcp-verdict"
    server_path = Path(__file__).parent / "fixtures" / "error_tool_server.py"
    config_path = tmp_path / "expected-error.yaml"
    config_path.write_text(
        "\n".join(
            [
                "server:",
                "  command:",
                f"    - {sys.executable}",
                f"    - {server_path}",
                "tool:",
                "  name: divide",
                "  arguments:",
                "    numerator: 1",
                "    denominator: 0",
                "expected: tool_error",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [str(cli_path), "check", "--config", str(config_path)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "PASS" in result.stdout


def test_check_fails_when_success_does_not_match_expected_tool_error(
    tmp_path: Path,
) -> None:
    """Report expected and actual outcomes when a success is unexpected."""
    cli_path = Path(sys.executable).parent / "mcp-verdict"
    server_path = Path(__file__).parents[1] / "examples" / "basic_stdio" / "server.py"
    config_path = tmp_path / "unexpected-success.yaml"
    config_path.write_text(
        "\n".join(
            [
                "server:",
                "  command:",
                f"    - {sys.executable}",
                f"    - {server_path}",
                "tool:",
                "  name: ping",
                "  arguments: {}",
                "expected: tool_error",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [str(cli_path), "check", "--config", str(config_path)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "FAIL" in result.stdout
    assert "Expected tool_error" in result.stdout
    assert "observed success" in result.stdout


@pytest.mark.parametrize(
    ("name", "contents"),
    [
        ("malformed", "server: [\n"),
        ("missing-fields", "server: {}\n"),
        ("unsupported-outcome", "expected: unknown\n"),
        (
            "invalid-arguments",
            "server:\n  command: [python]\ntool:\n  name: ping\n  arguments: []\nexpected: success\n",
        ),
    ],
)
def test_invalid_configurations_return_actionable_errors(
    tmp_path: Path, name: str, contents: str
) -> None:
    """Reject invalid YAML configurations without starting an MCP server."""
    cli_path = Path(sys.executable).parent / "mcp-verdict"
    config_path = tmp_path / f"{name}.yaml"
    config_path.write_text(contents, encoding="utf-8")

    result = subprocess.run(
        [str(cli_path), "check", "--config", str(config_path)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "error:" in result.stderr
    assert "Traceback" not in result.stderr


def test_missing_config_uses_setup_error_exit_code(tmp_path: Path) -> None:
    """Use exit code 2 for a configuration/setup failure."""
    cli_path = Path(sys.executable).parent / "mcp-verdict"
    missing_path = tmp_path / "missing.yaml"

    result = subprocess.run(
        [str(cli_path), "check", "--config", str(missing_path)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "error:" in result.stderr


def test_unreadable_config_uses_setup_error_exit_code(tmp_path: Path) -> None:
    """Use exit code 2 when the configuration path cannot be read."""
    cli_path = Path(sys.executable).parent / "mcp-verdict"
    config_path = tmp_path / "config-directory"
    config_path.mkdir()

    result = subprocess.run(
        [str(cli_path), "check", "--config", str(config_path)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "error:" in result.stderr
    assert "Traceback" not in result.stderr


def test_check_runs_multiple_scenarios_and_reports_summary(tmp_path: Path) -> None:
    """Run scenarios in order and fail overall when one outcome mismatches."""
    cli_path = Path(sys.executable).parent / "mcp-verdict"
    server_path = Path(__file__).parents[1] / "examples" / "basic_stdio" / "server.py"
    config_path = tmp_path / "scenarios.yaml"
    config_path.write_text(
        "\n".join(
            [
                "checks:",
                "  - name: ping-success",
                "    server:",
                "      command:",
                f"        - {sys.executable}",
                f"        - {server_path}",
                "    tool:",
                "      name: ping",
                "      arguments: {}",
                "    expected: success",
                "  - name: unexpected-success",
                "    server:",
                "      command:",
                f"        - {sys.executable}",
                f"        - {server_path}",
                "    tool:",
                "      name: ping",
                "      arguments: {}",
                "    expected: tool_error",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [str(cli_path), "check", "--config", str(config_path)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout.index("ping-success") < result.stdout.index("unexpected-success")
    assert "Summary: 1 passed, 1 failed" in result.stdout


def test_initialization_timeout_returns_setup_error(tmp_path: Path) -> None:
    """Return exit code 2 when initialization exceeds the configured timeout."""
    cli_path = Path(sys.executable).parent / "mcp-verdict"
    server_path = Path(__file__).parent / "fixtures" / "unresponsive_stdio_server.py"
    config_path = tmp_path / "initialization-timeout.yaml"
    config_path.write_text(
        f"server:\n  command: [{sys.executable}, {server_path}]\n"
        "tool:\n  name: never\n  arguments: {}\nexpected: success\ntimeout: 0.2\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [str(cli_path), "check", "--config", str(config_path)],
        check=False,
        capture_output=True,
        text=True,
        timeout=8,
    )

    assert result.returncode == 2
    assert "timed out" in result.stderr


def test_tool_timeout_returns_setup_error(tmp_path: Path) -> None:
    """Return exit code 2 when tool execution exceeds the configured timeout."""
    cli_path = Path(sys.executable).parent / "mcp-verdict"
    server_path = Path(__file__).parent / "fixtures" / "slow_tool_server.py"
    config_path = tmp_path / "tool-timeout.yaml"
    config_path.write_text(
        f"server:\n  command: [{sys.executable}, {server_path}]\n"
        "tool:\n  name: slow\n  arguments: {}\nexpected: success\ntimeout: 0.2\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [str(cli_path), "check", "--config", str(config_path)],
        check=False,
        capture_output=True,
        text=True,
        timeout=4,
    )

    assert result.returncode == 2
    assert "timed out" in result.stderr


@pytest.mark.parametrize(
    ("name", "server"),
    [
        ("missing-executable", ["mcp-verdict-no-such-server"]),
        (
            "exiting-server",
            [sys.executable, str(Path(__file__).parent / "fixtures" / "exiting_stdio_server.py")],
        ),
        (
            "disconnecting-server",
            [
                sys.executable,
                str(Path(__file__).parent / "fixtures" / "disconnecting_tool_server.py"),
            ],
        ),
    ],
)
def test_transport_failures_return_setup_error(
    tmp_path: Path, name: str, server: list[str]
) -> None:
    """Report expected transport failures without a raw traceback."""
    cli_path = Path(sys.executable).parent / "mcp-verdict"
    command = ", ".join(server)
    tool_name = "disconnect" if name == "disconnecting-server" else "ping"
    config_path = tmp_path / f"{name}.yaml"
    config_path.write_text(
        f"server:\n  command: [{command}]\n"
        f"tool:\n  name: {tool_name}\n  arguments: {{}}\nexpected: success\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [str(cli_path), "check", "--config", str(config_path)],
        check=False,
        capture_output=True,
        text=True,
        timeout=5,
    )

    assert result.returncode == 2
    assert "error:" in result.stderr
    assert "Traceback" not in result.stderr


def test_multiple_checks_continue_after_transport_error(tmp_path: Path) -> None:
    """Continue independent checks and summarize transport errors separately."""
    cli_path = Path(sys.executable).parent / "mcp-verdict"
    server_path = Path(__file__).parents[1] / "examples" / "basic_stdio" / "server.py"
    config_path = tmp_path / "transport-and-success.yaml"
    config_path.write_text(
        "\n".join(
            [
                "checks:",
                "  - name: missing-server",
                "    server:",
                "      command: [mcp-verdict-no-such-server]",
                "    tool: {name: ping, arguments: {}}",
                "    expected: success",
                "  - name: later-success",
                "    server:",
                "      command:",
                f"        - {sys.executable}",
                f"        - {server_path}",
                "    tool: {name: ping, arguments: {}}",
                "    expected: success",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [str(cli_path), "check", "--config", str(config_path)],
        check=False,
        capture_output=True,
        text=True,
        timeout=5,
    )

    assert result.returncode == 2
    assert "error: missing-server:" in result.stderr
    assert "later-success: PASS" in result.stdout
    assert "Summary: 1 passed, 0 failed, 1 errored" in result.stdout
