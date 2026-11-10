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


def _parse_check(data: Any, *, name: str = "check") -> CheckConfig:
    """Validate one decoded check mapping."""
    if not isinstance(data, dict):
        raise ValueError(f"Check {name!r} must be a YAML mapping")
    server = data.get("server")
    tool = data.get("tool")
    if not isinstance(server, dict) or not isinstance(tool, dict):
        raise ValueError(f"Check {name!r} requires 'server' and 'tool' mappings")

    command = server.get("command")
    tool_name = tool.get("name")
    arguments = tool.get("arguments", {})
    expected = data.get("expected")
    timeout = data.get("timeout")
    if not isinstance(command, list) or not command or not all(
        isinstance(item, str) for item in command
    ):
        raise ValueError(f"Check {name!r}: server.command must be a non-empty list")
    if not isinstance(tool_name, str) or not tool_name:
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

    return CheckConfig(command, tool_name, arguments, expected_outcome, name, timeout)


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
        configs.append(_parse_check(check, name=name))
    return configs
