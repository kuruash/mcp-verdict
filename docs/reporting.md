# Reporting

Human-readable terminal output is the default:

```bash
mcp-verdict check --config examples/basic_stdio/verdict.yaml
```

Use JSON for CI or downstream tooling:

```bash
mcp-verdict check --config examples/basic_stdio/verdict.yaml --format json
mcp-verdict check --config examples/basic_stdio/verdict.yaml \
  --format json --output reports/verdict.json
```

Without `--output`, exactly one JSON document is written to stdout. With
`--output`, the report is written atomically, parent directories are created,
and stdout remains empty on success. An explicitly selected existing file is
replaced. A report-write failure exits 2 and emits a safe error envelope.

## Schema version 1

```json
{
  "schema_version": "1",
  "summary": {"passed": 1, "failed": 0, "errored": 0},
  "checks": [{
    "name": "ping",
    "status": "PASS",
    "expected": "success",
    "actual": "success",
    "message": "Expected and observed success",
    "diagnostic_code": null,
    "expected_http_status": null,
    "actual_http_status": null
  }]
}
```

Execution errors use `status: "ERROR"` and `actual: null`. Global
configuration errors use a versioned `error` envelope. HTTP status checks also
include their expected and observed status fields.

Diagnostic categories include `outcome_mismatch`, `tool_error`, `timeout`,
`initialization_failure`, `transport_disconnect`, `authentication_failure`,
`authorization_failure`, and `http_status_mismatch`. Messages are bounded and
common token/password/secret/bearer patterns are redacted. Reports never store
full environments, Authorization headers, or unrestricted MCP payloads.

## GitHub Actions

```yaml
- run: mcp-verdict check --config verdict.yaml --format json --output verdict.json
- uses: actions/upload-artifact@v4
  with:
    name: mcp-verdict-report
    path: verdict.json
```
