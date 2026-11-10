"""Adversarial tests for safe diagnostic evidence."""

from mcp_verdict.reporting.diagnostics import MAX_MESSAGE_LENGTH, safe_message


def test_diagnostics_redact_credentials_and_bound_length() -> None:
    """Never emit common credential-shaped values or unbounded messages."""
    secret = "sk-live-123456"
    message = (
        f"token={secret} password=hunter2 bearer BearerXYZ "
        f"api_key=key-123 credential=cred-456 {secret} " + "x" * 500
    )

    safe = safe_message(message)

    assert secret not in safe
    assert "hunter2" not in safe
    assert "BearerXYZ" not in safe
    assert "key-123" not in safe
    assert "cred-456" not in safe
    assert len(safe) == MAX_MESSAGE_LENGTH
