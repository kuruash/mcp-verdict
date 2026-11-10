# Incorrect Error Handling Example

This example is intentionally incorrect. Its `known_failure` tool returns text
describing a failure but sends an MCP result with `isError: false`. MCP Verdict
uses the explicit protocol field, so it detects the mismatch instead of
inferring an error from the text.

Install MCP Verdict from the repository root:

```bash
python -m pip install -e '.[test]'
```

Run the intentional failure scenario:

```bash
mcp-verdict check --config examples/error_handling/verdict.yaml
```

The command is expected to print:

```text
known-failure: FAIL: Expected tool_error, observed success
Summary: 0 passed, 1 failed
```

It intentionally exits with status `1`, because the server's error reporting is
incorrect.

## Security note

`verdict.yaml` launches a local command with the current user's permissions.
Run only trusted configurations; MCP Verdict intentionally does not sandbox
configured server commands.
