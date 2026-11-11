# Transports

MCP Verdict keeps transport lifecycle separate from tool execution and
reporting. Both transports yield an initialized official MCP SDK session.

## STDIO

`mcp_verdict/stdio.py` launches the configured executable through the SDK's
STDIO client, initializes a `ClientSession`, and closes the session and process
when the context exits. Initialization and tool execution are bounded by the
configured timeout. Existing configurations default to this transport.

## Streamable HTTP

`mcp_verdict/http.py` uses `mcp.client.streamable_http.streamable_http_client`
from the installed MCP Python SDK. It supports HTTP and HTTPS endpoint URLs,
bounded initialization, and environment-based bearer headers. The SDK owns MCP
message parsing and session behavior; MCP Verdict does not implement a second
HTTP or JSON-RPC stack.

The project is tested with MCP Python SDK 1.30.0 and the protocol behavior
exposed by that SDK (protocol constant `2025-11-25`). Later protocol revisions,
including stateless behavior not exposed by this SDK, are not claimed as
supported.

HTTP clients do not automatically follow redirects. The SDK permits only its
documented same-origin behavior, and MCP Verdict rejects endpoint URLs that
contain embedded userinfo credentials.

## Troubleshooting

- `Could not start MCP server`: verify the executable and its arguments.
- `MCP HTTP URL ...`: check the scheme, hostname, and endpoint path.
- `Required authentication environment variable ... is unset`: export the
  named variable without placing the token in YAML.
- Timeout or transport ERROR: confirm the server is running, responsive, and
  reachable from the local environment.
