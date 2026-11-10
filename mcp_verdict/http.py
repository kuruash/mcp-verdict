"""Streamable HTTP MCP connections using the official MCP SDK transport."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
import os
import logging
from urllib.parse import urlparse

import anyio
import httpx
from mcp import ClientSession, InitializeResult
from mcp.client.streamable_http import streamable_http_client


@dataclass(frozen=True)
class HttpConnection:
    """Initialized MCP session and negotiated initialization response."""

    session: ClientSession
    initialize_result: InitializeResult


def validate_url(url: str) -> None:
    """Validate an MCP Streamable HTTP URL before opening a connection."""
    parsed = urlparse(url)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
    ):
        raise ValueError("MCP HTTP URL must use http:// or https:// with a hostname")


@asynccontextmanager
async def connect_to_http_server(
    url: str, *, timeout: float = 10.0, auth_env: str | None = None
) -> AsyncIterator[HttpConnection]:
    """Connect to and initialize an MCP Streamable HTTP server.

    Args:
        url: HTTP or HTTPS MCP endpoint URL.
        timeout: Maximum seconds allowed for initialization and transport setup.

    Yields:
        An initialized live MCP session and initialization response.

    Raises:
        ValueError: If ``url`` is malformed or uses an unsupported scheme.
        TimeoutError: If initialization exceeds ``timeout`` seconds.
        httpx.HTTPError: If the endpoint cannot be reached or rejects a request.
    """
    validate_url(url)
    sdk_logger = logging.getLogger("mcp.client.streamable_http")
    was_disabled = sdk_logger.disabled
    sdk_logger.disabled = True
    headers: dict[str, str] = {}
    if auth_env is not None:
        token = os.environ.get(auth_env)
        if not token:
            raise ValueError(f"Required authentication environment variable {auth_env!r} is unset")
        headers["Authorization"] = f"Bearer {token}"
    client_timeout = httpx.Timeout(timeout)
    try:
        async with httpx.AsyncClient(
            timeout=client_timeout, follow_redirects=False, headers=headers
        ) as client:
            async with streamable_http_client(
                url, http_client=client, terminate_on_close=False
            ) as (read_stream, write_stream, _get_session_id):
                async with ClientSession(read_stream, write_stream) as session:
                    try:
                        with anyio.fail_after(timeout):
                            initialize_result = await session.initialize()
                    except TimeoutError:
                        raise
                    except Exception as exc:
                        raise ConnectionError(
                            "MCP HTTP initialization returned an invalid response"
                        ) from exc
                    yield HttpConnection(session, initialize_result)
    finally:
        sdk_logger.disabled = was_disabled


async def probe_http_status(
    url: str, *, timeout: float = 10.0, auth_env: str | None = None
) -> int:
    """Probe an HTTP endpoint and return its status without parsing MCP payloads."""
    validate_url(url)
    headers: dict[str, str] = {}
    if auth_env is not None:
        token = os.environ.get(auth_env)
        if not token:
            raise ValueError(f"Required authentication environment variable {auth_env!r} is unset")
        headers["Authorization"] = f"Bearer {token}"
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(timeout), follow_redirects=False, headers=headers
    ) as client:
        response = await client.post(url, content=b"{}")
        return response.status_code
