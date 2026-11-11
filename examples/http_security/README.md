# HTTP security example

This example is a local-only Streamable HTTP MCP server with a synthetic bearer
token policy. It is not an OAuth or JWT implementation and does not validate
remote security systems.

Install MCP Verdict from the repository root:

```bash
python -m pip install -e '.[test]'
```

Start the server on loopback in one terminal:

```bash
python examples/http_security/server.py 8000
```

In another terminal, run the authenticated tool check:

```bash
export MCP_VERDICT_EXAMPLE_TOKEN=valid-token
mcp-verdict check --config examples/http_security/verdict.yaml
```

It exits `0` and reports `PASS`. To test an expected unauthenticated response,
run:

```bash
mcp-verdict check --config examples/http_security/unauthenticated.yaml
```

That check also exits `0` because HTTP 401 is the declared expected result.
Credentials are read from the named environment variable and are never placed
in YAML or reports. Bindings are restricted to `127.0.0.1`; stop the server
with Ctrl-C when finished.

To demonstrate authorization separately, use a valid-but-limited synthetic
identity:

```bash
export MCP_VERDICT_EXAMPLE_TOKEN=limited-token
mcp-verdict check --config examples/http_security/forbidden.yaml
```

This also exits `0` because the declared expected response is HTTP 403. An
invalid token receives HTTP 401; `limited-token` is authenticated but lacks the
permission required by the fixture policy.
