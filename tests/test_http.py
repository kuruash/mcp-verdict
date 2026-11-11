"""Integration tests for real local Streamable HTTP MCP connections."""

import socket
import subprocess
import sys
import time
from pathlib import Path

import anyio
import pytest

from mcp_verdict.http import connect_to_http_server, validate_url
from mcp_verdict.tools import execute_tool


FIXTURE = Path(__file__).parent / "fixtures" / "http_stdio_server.py"


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@pytest.fixture
def http_server():
    """Start and reliably terminate a local Streamable HTTP fixture."""
    port = _free_port()
    process = subprocess.Popen([sys.executable, str(FIXTURE), str(port)])
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        with socket.socket() as sock:
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                break
        time.sleep(0.05)
    else:
        process.kill()
        process.wait()
        raise RuntimeError("HTTP fixture did not start")
    try:
        yield f"http://127.0.0.1:{port}/mcp"
    finally:
        process.terminate()
        process.wait(timeout=5)


def test_http_connection_initializes_and_executes_tool(http_server: str) -> None:
    """Connect through the official SDK and execute a real MCP tool."""

    async def exercise() -> None:
        async with connect_to_http_server(http_server) as connection:
            result = await execute_tool(connection.session, "ping")
            assert result.isError is False

    anyio.run(exercise)


def test_http_url_validation_rejects_unsupported_schemes() -> None:
    """Reject malformed and non-HTTP endpoint URLs before network access."""
    with pytest.raises(ValueError):
        validate_url("file:///tmp/server")
    with pytest.raises(ValueError):
        validate_url("http:///missing-host")
    with pytest.raises(ValueError):
        validate_url("https://user:password@example.test/mcp")


def test_http_unavailable_endpoint_fails_cleanly() -> None:
    """Raise an SDK HTTP error for an unavailable local endpoint."""

    async def exercise() -> None:
        with pytest.raises(Exception):
            async with connect_to_http_server("http://127.0.0.1:1/mcp", timeout=0.2):
                pass

    anyio.run(exercise)
