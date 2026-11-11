"""YAML configuration loading and validation for MCP Verdict checks."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from mcp_verdict.outcomes import ToolOutcome


@dataclass(frozen=True)
class CheckConfig:
    """Validated configuration for one MCP tool check."""

    command: list[str]
    tool_name: str
    arguments: dict[str, Any]
    expected: ToolOutcome
    name: str = "check"
    timeout: float | None = None
    transport: str = "stdio"
    url: str | None = None
    auth_env: str | None = None
    expected_http_status: int | None = None


def _parse_check(data: Any, *, name: str = "check") -> CheckConfig:
    """Validate one decoded check mapping."""
    if not isinstance(data, dict):
        raise ValueError(f"Check {name!r} must be a YAML mapping")
    server = data.get("server")
    tool = data.get("tool")
    if not isinstance(server, dict):
        raise ValueError(f"Check {name!r} requires a 'server' mapping")

    command = server.get("command")
    transport = server.get("transport", "stdio")
    url = server.get("url")
    auth_env = server.get("auth_env")
    expected_http_status = data.get("expected_http_status")
    if expected_http_status is not None and (
        isinstance(expected_http_status, bool)
        or not isinstance(expected_http_status, int)
        or not 100 <= expected_http_status <= 599
    ):
        raise ValueError(f"Check {name!r}: expected_http_status must be 100..599")
    tool = data.get("tool")
    if expected_http_status is None and not isinstance(tool, dict):
        raise ValueError(f"Check {name!r} requires a 'tool' mapping")
    tool = tool if isinstance(tool, dict) else {}
    tool_name = tool.get("name", "")
    arguments = tool.get("arguments", {})
    expected = data.get("expected", "success" if expected_http_status is not None else None)
    timeout = data.get("timeout")
    if transport not in {"stdio", "streamable_http"}:
        raise ValueError(
            f"Check {name!r}: server.transport must be 'stdio' or 'streamable_http'"
        )
    if transport == "stdio":
        if not isinstance(command, list) or not command or not all(
            isinstance(item, str) for item in command
        ):
            raise ValueError(f"Check {name!r}: server.command must be a non-empty list")
        if "url" in server:
            raise ValueError(f"Check {name!r}: stdio server cannot define server.url")
        if "auth_env" in server:
            raise ValueError(
                f"Check {name!r}: stdio server cannot define server.auth_env"
            )
    else:
        if not isinstance(url, str) or not url:
            raise ValueError(f"Check {name!r}: HTTP server requires server.url")
        if "command" in server:
            raise ValueError(f"Check {name!r}: HTTP server cannot define server.command")
        command = []
    if not isinstance(tool_name, str) or not tool_name:
        if expected_http_status is None:
            raise ValueError(f"Check {name!r}: tool.name must be a non-empty string")
    if not isinstance(arguments, dict):
        raise ValueError(f"Check {name!r}: tool.arguments must be a mapping")
    if timeout is not None and (
        isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or timeout <= 0
    ):
        raise ValueError(f"Check {name!r}: timeout must be a positive number")
    try:
        expected_outcome = ToolOutcome(expected)
    except ValueError as exc:
        raise ValueError(
            f"Check {name!r}: expected must be 'success' or 'tool_error'"
        ) from exc

    if auth_env is not None and (not isinstance(auth_env, str) or not auth_env):
        raise ValueError(f"Check {name!r}: server.auth_env must be a non-empty string")
    return CheckConfig(
        command,
        tool_name,
        arguments,
        expected_outcome,
        name,
        timeout,
        transport,
        url,
        auth_env,
        expected_http_status,
    )


def _read_config(path: Path) -> Any:
    """Read and decode a YAML configuration file."""
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML configuration: {exc}") from exc


def load_config(path: Path) -> CheckConfig:
    """Load and validate one YAML check configuration.

    Args:
        path: YAML configuration path.

    Returns:
        Validated check configuration.

    Raises:
        ValueError: If the file cannot be parsed or has invalid fields.
        OSError: If the file cannot be read.
    """
    data = _read_config(path)
    if isinstance(data, dict) and "checks" in data:
        raise ValueError("Configuration contains multiple checks")
    return _parse_check(data)


def load_configs(path: Path) -> list[CheckConfig]:
    """Load one or more named checks from a YAML configuration."""
    data = _read_config(path)
    if not isinstance(data, dict):
        raise ValueError("Configuration must be a YAML mapping")
    if "checks" not in data:
        return [_parse_check(data)]
    checks = data["checks"]
    if not isinstance(checks, list) or not checks:
        raise ValueError("checks must be a non-empty list")
    configs = []
    for index, check in enumerate(checks, start=1):
        if not isinstance(check, dict):
            raise ValueError(f"Check {index} must be a YAML mapping")
        name = check.get("name", f"check-{index}")
        if not isinstance(name, str) or not name:
            raise ValueError(f"Check {index}: name must be a non-empty string")
        if "server" not in check and "server" in data:
            check = {**check, "server": data["server"]}
        configs.append(_parse_check(check, name=name))
    return configs
