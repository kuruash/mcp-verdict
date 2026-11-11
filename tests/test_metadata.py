"""Package metadata consistency checks."""

import importlib.metadata

import mcp_verdict


def test_runtime_version_matches_distribution_metadata() -> None:
    """Expose the same version declared in the built package metadata."""
    assert mcp_verdict.__version__ == importlib.metadata.version("mcp-verdict")
    assert mcp_verdict.__version__ == "0.1.0"
