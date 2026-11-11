# Configuration

MCP Verdict reads YAML files with `mcp-verdict check --config PATH`. A file can
describe one check or an ordered `checks` list. A top-level `server` mapping is
shared by checks; a check may provide its own server mapping instead.

## STDIO check

```yaml
server:
  command: [python, examples/basic_stdio/server.py]
tool:
  name: ping
  arguments: {}
expected: success
timeout: 10
```

`command` is a non-empty executable-and-arguments list. Omitting
`server.transport` means `stdio`. `tool.arguments` must be a YAML mapping and
is passed to the MCP SDK unchanged. `expected` is `success` or `tool_error`,
based on the tool result's explicit `isError` field.

## Multiple checks

```yaml
server:
  command: [python, examples/basic_stdio/server.py]
checks:
  - name: ping-check
    tool:
      name: ping
      arguments: {}
    expected: success
  - name: add-check
    tool:
      name: add
      arguments: {a: 7, b: 5}
    expected: success
```

Checks run sequentially in file order. A recoverable check error does not stop
later checks; the summary and exit code retain the error.

## Streamable HTTP

```yaml
server:
  transport: streamable_http
  url: http://127.0.0.1:8000/mcp
  auth_env: MCP_VERDICT_TOKEN
tool:
  name: ping
  arguments: {}
expected: success
timeout: 10
```

`url` must use `http` or `https` and include a hostname. `auth_env` names an
environment variable containing a synthetic bearer token; the token itself
must not be placed in YAML. STDIO and HTTP fields cannot be mixed.

For an HTTP denial check, omit `tool` and declare the observed status:

```yaml
server:
  transport: streamable_http
  url: http://127.0.0.1:8000/mcp
expected_http_status: 401
```

The status must be an integer from 100 through 599. Matching status is PASS;
an unexpected status is FAIL; an unreachable endpoint is ERROR. This assertion
is separate from MCP tool-level errors.

## Validation and safety

Missing mappings, malformed commands, unsupported transports, invalid URLs,
invalid expected outcomes, and non-positive timeouts are configuration errors
and exit with status 2. `server.command` executes locally with the current
user's permissions. Only run trusted configurations; see [Security](../SECURITY.md).

Runnable files are in [examples](../examples/).
