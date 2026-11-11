# Security policy

MCP Verdict is an early-stage developer testing tool. It is not a complete
OAuth, JWT, authorization, compliance, or vulnerability scanner.

## Supported versions

Only the latest code on the default branch is currently maintained. There are
no published security-support guarantees for older versions before the first
stable release.

## Reporting a vulnerability

Please report suspected vulnerabilities privately to the repository maintainers
through a security contact mechanism available on the repository hosting
service. Do not publish exploit details or a public issue before maintainers
have had an opportunity to coordinate handling.

Do not include real credentials, customer data, or production endpoints in a
report. Synthetic reproductions and minimal local fixtures are preferred.

## Scope and boundaries

The YAML `server.command` value executes a local process with the current
user's permissions. Treat configurations as executable input and never run an
untrusted file. HTTP checks are intended for servers you own or are authorized
to test; the project does not discover targets, guess credentials, or attack
third-party systems.

MCP Verdict redacts common credential-shaped diagnostic values and omits raw
tool payloads, but arbitrary third-party output cannot be perfectly sanitized.
Use isolated environments and synthetic credentials for security testing.
