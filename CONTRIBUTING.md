# Contributing to MCP Verdict

## Development setup

MCP Verdict supports Python 3.11 and 3.12. From a checkout:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[test]'
```

Run the complete checks with:

```bash
python -m pytest -q
ruff check .
ruff format --check .
mypy mcp_verdict
python -m build
python -m twine check dist/*
```

## Development expectations

New behavior follows RED → GREEN → REFACTOR. Add a focused failing test first,
implement the smallest correction, then simplify without weakening assertions.
Use real local MCP fixtures for transport behavior. Fixtures must bind to
loopback, use deterministic data, enforce bounded timeouts, and clean up their
subprocesses.

Keep transport, execution, reporting, and CLI responsibilities separate. Use
type hints and Google-style docstrings for public functions. Never put tokens,
credentials, full environments, or unrestricted MCP payloads into reports.

To add a scenario, create a fixture under `tests/fixtures/`, add an integration
test with a descriptive name and cleanup fixture, and preserve existing STDIO,
HTTP, JSON, and exit-code tests.

Pull requests should describe the behavior changed, include exact test output,
call out compatibility or security impact, and update documentation for any
user-visible configuration or command.
