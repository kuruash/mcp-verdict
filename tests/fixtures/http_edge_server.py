"""Deterministic loopback HTTP fixture for transport regression tests."""

import json
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Handler(BaseHTTPRequestHandler):
    """Serve one deliberately controlled HTTP behavior."""

    mode = "status"

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        if self.mode == "origin" and self.headers.get("Origin") != "http://allowed.test":
            self.send_response(403)
            self.end_headers()
            return
        self.send_response(405)
        self.end_headers()

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler API
        if self.mode == "status":
            self._respond(400)
        elif self.mode == "not-found":
            self._respond(404)
        elif self.mode == "method":
            self._respond(405)
        elif self.mode == "server-error":
            self._respond(500)
        elif self.mode == "invalid-json":
            self._respond(200, b"{not-json", "application/json")
            os._exit(0)
        elif self.mode == "invalid-rpc":
            self._respond(200, b"{}", "application/json")
            os._exit(0)
        elif self.mode == "content-type":
            self._respond(200, b"{}", "text/plain")
            os._exit(0)
        elif self.mode == "truncated":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", "100")
            self.end_headers()
            self.wfile.write(b"{}")
            self.wfile.flush()
            self.connection.close()
            os._exit(0)
        elif self.mode == "slow":
            time.sleep(5)
            self._respond(500)
        elif self.mode == "disconnect":
            self.connection.close()
        elif self.mode == "protocol-version":
            self._respond(
                200,
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": 0,
                        "error": {"code": -32600, "message": "unsupported protocol version"},
                    }
                ).encode(),
                "application/json",
            )
        elif self.mode == "redirect":
            self.send_response(307)
            self.send_header("Location", "http://127.0.0.1:9/mcp")
            self.end_headers()
        else:
            self._respond(404)

    def _respond(self, status: int, body: bytes = b"", content_type: str = "text/plain") -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if body:
            self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:
        """Keep fixture diagnostics out of test output."""


if __name__ == "__main__":
    port, mode = int(sys.argv[1]), sys.argv[2]
    Handler.mode = mode
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
