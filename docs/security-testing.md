# Security testing

Security checks are explicit, local or user-authorized behavior tests. They do
not constitute an OAuth/JWT audit or a compliance certification.

## Authentication versus authorization

HTTP status assertions distinguish the boundaries:

- Missing or invalid credentials commonly produce HTTP 401 and a challenge.
- An authenticated identity without permission can produce HTTP 403.
- A correctly authorized identity can initialize MCP and call a tool.

The local HTTP example uses synthetic identities to demonstrate these cases.
Its policy is fixture-specific; a 401 or 403 does not universally prove that a
remote server is secure.

MCP tool results are separate. A tool returning `isError: true` is a tool-level
outcome, not automatically an HTTP 401 or 403.

## Credentials and redirects

Reference credentials with `server.auth_env` and export the named environment
variable in the shell or CI secret store. Do not put tokens in YAML, command
arguments, reports, or issue tickets. HTTP redirects are not blindly followed,
and cross-origin credentials must not be forwarded.

## Authorized scope

Test only servers you own or are authorized to assess. Bind local fixtures to
loopback, use synthetic credentials, and clean up server processes. MCP Verdict
does not discover targets, guess credentials, or contact third-party services.

## Limitations

The project tests the official MCP SDK transport and selected HTTP responses.
It does not implement a complete OAuth provider, JWT verifier, token-expiry
model, or universal protocol compatibility layer. Diagnostic messages are
bounded and redact common credential-shaped strings, but arbitrary third-party
output cannot be perfectly sanitized; unrestricted payloads are omitted.
