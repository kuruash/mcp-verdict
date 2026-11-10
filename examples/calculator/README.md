# Calculator Example

This example is a local FastMCP server with typed arithmetic tools:

- `add` accepts two numbers and returns their sum.
- `divide` accepts a numerator and a nonzero denominator.
- `divide` raises a tool error when the denominator is zero.

Install MCP Verdict from the repository root:

```bash
python -m pip install -e '.[test]'
```

Run the configured checks from the repository root:

```bash
mcp-verdict check --config examples/calculator/verdict.yaml
```

Expected output includes three PASS lines and:

```text
Summary: 3 passed, 0 failed
```

The divide-by-zero case is expected to be a tool error, so the complete command
still exits with status 0.

## Security note

`verdict.yaml` executes its configured local command with the current user's
permissions. Use only trusted YAML files; MCP Verdict does not sandbox server
commands.
