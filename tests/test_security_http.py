"""Local authentication and authorization assertion integration tests."""

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

FIXTURE = Path(__file__).parent / "fixtures" / "auth_http_server.py"
CLI = Path(sys.executable).parent / "mcp-verdict"


@pytest.fixture
def auth_endpoint():
    """Start the deterministic local authentication fixture."""
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = int(sock.getsockname()[1])
    process = subprocess.Popen([sys.executable, str(FIXTURE), str(port)])
    try:
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            with socket.socket() as probe:
                if probe.connect_ex(("127.0.0.1", port)) == 0:
                    break
            time.sleep(0.05)
        else:
            process.kill()
            process.wait()
            raise RuntimeError("authentication fixture did not start")
        yield f"http://127.0.0.1:{port}/mcp"
    finally:
        process.terminate()
        process.wait(timeout=5)


def _run(config: Path, *, token: str | None = None):
    environment = os.environ.copy()
    if token is not None:
        environment["MCP_VERDICT_TEST_TOKEN"] = token
    return subprocess.run(
        [str(CLI), "check", "--config", str(config)],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
        timeout=10,
    )


def test_expected_authentication_denial_passes(auth_endpoint: str, tmp_path: Path) -> None:
    """Pass an explicit 401 expectation without exposing credentials."""
    config = tmp_path / "auth.yaml"
    config.write_text(
        f"server:\n  transport: streamable_http\n  url: {auth_endpoint}\n"
        "checks:\n  - name: unauthenticated\n    expected_http_status: 401\n",
        encoding="utf-8",
    )
    result = _run(config)
    assert result.returncode == 0
    assert "Expected HTTP 401, observed HTTP 401" in result.stdout


def test_valid_token_allows_mcp_check(auth_endpoint: str, tmp_path: Path) -> None:
    """Read a bearer token from an environment variable for MCP execution."""
    config = tmp_path / "auth.yaml"
    config.write_text(
        f"server:\n  transport: streamable_http\n  url: {auth_endpoint}\n  auth_env: MCP_VERDICT_TEST_TOKEN\n"
        "tool:\n  name: ping\n  arguments: {}\nexpected: success\n",
        encoding="utf-8",
    )
    result = _run(config, token="valid-token")
    assert result.returncode == 0
    assert "PASS" in result.stdout
    assert "valid-token" not in result.stdout


def test_invalid_token_matches_expected_unauthorized_status(
    auth_endpoint: str, tmp_path: Path
) -> None:
    """Distinguish an expected HTTP 401 from an MCP tool error."""
    config = tmp_path / "invalid.yaml"
    config.write_text(
        f"server:\n  transport: streamable_http\n  url: {auth_endpoint}\n  auth_env: MCP_VERDICT_TEST_TOKEN\n"
        "expected_http_status: 401\n",
        encoding="utf-8",
    )
    result = _run(config, token="invalid-token")
    assert result.returncode == 0
    assert "Expected HTTP 401, observed HTTP 401" in result.stdout


def test_limited_identity_matches_expected_forbidden_status(
    auth_endpoint: str, tmp_path: Path
) -> None:
    """Return 403 for an authenticated identity lacking permission."""
    config = tmp_path / "forbidden.yaml"
    config.write_text(
        f"server:\n  transport: streamable_http\n  url: {auth_endpoint}\n  auth_env: MCP_VERDICT_TEST_TOKEN\n"
        "expected_http_status: 403\n",
        encoding="utf-8",
    )
    result = _run(config, token="limited-token")
    assert result.returncode == 0
    assert "Expected HTTP 403, observed HTTP 403" in result.stdout


def test_missing_auth_environment_variable_is_safe_error(
    auth_endpoint: str, tmp_path: Path
) -> None:
    """Reject an unset credential reference without printing credentials."""
    config = tmp_path / "missing-env.yaml"
    config.write_text(
        f"server:\n  transport: streamable_http\n  url: {auth_endpoint}\n  auth_env: MCP_VERDICT_NOT_SET\n"
        "tool:\n  name: ping\n  arguments: {}\nexpected: success\n",
        encoding="utf-8",
    )
    result = _run(config)
    assert result.returncode == 2
    assert "unset" in result.stderr
