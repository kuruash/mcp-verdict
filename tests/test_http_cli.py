"""CLI integration coverage for HTTP transport configuration."""

import socket
import subprocess
import sys
import time
from pathlib import Path


def test_cli_runs_streamable_http_check(tmp_path: Path) -> None:
    """Run a configured HTTP MCP check through the installed CLI."""
    fixture = Path(__file__).parent / "fixtures" / "http_stdio_server.py"
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = int(sock.getsockname()[1])
    server = subprocess.Popen([sys.executable, str(fixture), str(port)])
    try:
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            with socket.socket() as probe:
                if probe.connect_ex(("127.0.0.1", port)) == 0:
                    break
            time.sleep(0.05)
        config = tmp_path / "http.yaml"
        config.write_text(
            f"server:\n  transport: streamable_http\n  url: http://127.0.0.1:{port}/mcp\n"
            "checks:\n  - name: ping-check\n    tool:\n      name: ping\n      arguments: {}\n    expected: success\n",
            encoding="utf-8",
        )
        cli = Path(sys.executable).parent / "mcp-verdict"
        result = subprocess.run(
            [str(cli), "check", "--config", str(config)],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "ping-check: PASS" in result.stdout
    finally:
        server.terminate()
        server.wait(timeout=5)
