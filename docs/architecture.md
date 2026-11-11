# Architecture overview

MCP Verdict has four layers:

- `mcp_verdict/stdio.py` and `mcp_verdict/http.py` own transport lifecycle and
  initialized SDK sessions.
- `mcp_verdict/tools.py` executes tools against a live session and preserves SDK
  results.
- `mcp_verdict/outcomes.py` compares explicit MCP `isError` outcomes.
- `mcp_verdict/reporting/` stores typed results, summaries, JSON serialization,
  and bounded diagnostics.
- `mcp_verdict/cli/` loads YAML, dispatches checks, and renders terminal/JSON
  output.

Tests use real local FastMCP or HTTP subprocess fixtures. Transport modules do
not depend on CLI presentation, and reporting does not capture commands,
environments, credentials, or unrestricted MCP payloads.
