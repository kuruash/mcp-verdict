"""Regression tests for controlled HTTP and protocol failures."""

import socket
import subprocess
import sys
import time
from pathlib import Path

import anyio
import pytest

from mcp_verdict.http import connect_to_http_server, probe_http_status

FIXTURE = Path(__file__).parent / "fixtures" / "http_edge_server.py"
CLI = Path(sys.executable).parent / "mcp-verdict"


@pytest.fixture
def edge_server():
    """Start an edge-case server and return a mode-specific endpoint factory."""
    processes: list[subprocess.Popen[bytes]] = []

    def start(mode: str) -> str:
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = int(sock.getsockname()[1])
        process = subprocess.Popen([sys.executable, str(FIXTURE), str(port), mode])
        processes.append(process)
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            with socket.socket() as probe:
                if probe.connect_ex(("127.0.0.1", port)) == 0:
                    return f"http://127.0.0.1:{port}/mcp"
            time.sleep(0.03)
        raise RuntimeError(f"fixture did not start: {mode}")

    yield start
    for process in processes:
        if process.poll() is None:
            process.terminate()
        process.wait(timeout=5)


@pytest.mark.parametrize(
    ("mode", "status"),
    [("status", 400), ("not-found", 404), ("method", 405), ("server-error", 500)],
)
def test_http_status_probe_returns_actual_status(edge_server, mode: str, status: int) -> None:
    """Assert controlled HTTP status responses without parsing exception text."""

    async def exercise() -> None:
        assert await probe_http_status(edge_server(mode), timeout=1) == status

    anyio.run(exercise)


@pytest.mark.parametrize("mode", ["invalid-json", "invalid-rpc", "content-type", "truncated"])
def test_malformed_http_responses_are_bounded_errors(edge_server, mode: str) -> None:
    """Convert malformed transport responses into bounded SDK failures."""

    async def exercise() -> None:
        with pytest.raises(Exception):
            async with connect_to_http_server(edge_server(mode), timeout=0.5):
                pass

    anyio.run(exercise)


@pytest.mark.parametrize("mode", ["slow", "disconnect", "protocol-version"])
def test_http_session_failures_do_not_hang(edge_server, mode: str) -> None:
    """Bound initialization failures from slow, disconnected, or invalid servers."""

    async def exercise() -> None:
        with pytest.raises(Exception):
            async with connect_to_http_server(edge_server(mode), timeout=0.5):
                pass

    anyio.run(exercise)


def test_invalid_origin_is_rejected_by_controlled_server(edge_server) -> None:
    """Verify an explicit invalid Origin policy at the fixture boundary."""
    import httpx

    async def exercise() -> None:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                edge_server("origin"), headers={"Origin": "http://invalid.test"}
            )
            assert response.status_code == 403

    anyio.run(exercise)


def test_cross_origin_redirect_fails_without_following(edge_server) -> None:
    """Reject redirects rather than forwarding authorization to another origin."""
    from mcp_verdict.http import connect_to_http_server

    async def exercise() -> None:
        with pytest.raises(Exception):
            async with connect_to_http_server(edge_server("redirect"), timeout=0.5):
                pass

    anyio.run(exercise)


@pytest.mark.parametrize("mode", ["invalid-json", "invalid-rpc", "content-type", "truncated"])
def test_cli_malformed_http_response_is_error(edge_server, mode: str, tmp_path: Path) -> None:
    """Return exit code 2 without leaking SDK tracebacks for malformed responses."""
    config = tmp_path / f"{mode}.yaml"
    config.write_text(
        f"server:\n  transport: streamable_http\n  url: {edge_server(mode)}\n"
        "tool:\n  name: ping\n  arguments: {}\nexpected: success\ntimeout: 0.5\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [str(CLI), "check", "--config", str(config)],
        check=False,
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 2
    assert "Traceback" not in result.stderr
    assert "invalid" in result.stderr.lower()
