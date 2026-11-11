"""Bounded redaction for diagnostic messages emitted by the CLI."""

import re

_SENSITIVE = re.compile(
    r"(?i)(bearer\s+|token\s*[=:]\s*|password\s*[=:]\s*|secret\s*[=:]\s*|api[_-]?key\s*[=:]\s*|credential\s*[=:]\s*)[^\s,;]+|\b(?:sk|ghp|xoxb)-[A-Za-z0-9_-]+"
)
MAX_MESSAGE_LENGTH = 240


def safe_message(message: str) -> str:
    """Redact common credential-shaped values and bound diagnostic length."""
    redacted = _SENSITIVE.sub(lambda match: f"{match.group(1) or ''}[REDACTED]", message)
    if len(redacted) > MAX_MESSAGE_LENGTH:
        return redacted[: MAX_MESSAGE_LENGTH - 3] + "..."
    return redacted
