# MCP Verdict


[![PyPI Version](https://img.shields.io/pypi/v/mcp-verdict)](https://pypi.org/project/mcp-verdict/)
[![Python Versions](https://img.shields.io/pypi/pyversions/mcp-verdict)](https://pypi.org/project/mcp-verdict/)
[![CI](https://github.com/kuruash/mcp-verdict/actions/workflows/ci.yml/badge.svg)](https://github.com/kuruash/mcp-verdict/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/kuruash/mcp-verdict/blob/main/LICENSE)
[![PyPI Downloads](https://img.shields.io/pypi/dm/mcp-verdict)](https://pypi.org/project/mcp-verdict/)


**Test how your MCP servers behave when things go wrong.**

MCP Verdict is an open-source Python CLI for testing failure handling and
selected security behavior in Model Context Protocol (MCP) servers. It runs
repeatable YAML-defined checks against servers you own or are authorized to
assess.

MCP Verdict is a test runner, not a general MCP client or a comprehensive
security scanner. It does not provide full OAuth/JWT auditing, compliance
certification, sandboxing, or remote target discovery.

## Why MCP Verdict?

MCP tools can fail in ways that are difficult to exercise repeatedly: a server
may return success while reporting a failure, omit an expected tool error, or
handle authentication and authorization boundaries incorrectly. These behaviors
can regress as a server changes.

MCP Verdict makes those cases explicit in version-controlled configuration.
Instead of maintaining one-off failure-testing scripts, developers can run the
same local STDIO or Streamable HTTP scenarios in development and CI.

## Features

- STDIO and Streamable HTTP MCP connections.
- MCP tool outcome assertions based on the protocol `isError` field.
- HTTP authentication and authorization status assertions, including 401 and
  403 expectations.
- YAML-defined single or multiple checks with per-check timeouts.
- PASS, FAIL, and ERROR results with CI-friendly exit codes.
- Human-readable terminal output and schema-versioned JSON reports.
- Atomic report files and bounded diagnostic redaction.

## Quick start

Requirements: Python 3.11 or 3.12. From the repository root:

```bash
python -m pip install -e .
mcp-verdict check --config examples/basic_stdio/verdict.yaml
```

The Basic STDIO example uses a local FastMCP server and needs no credentials or
network access. Its output is:

```text
ping-success: PASS: Expected and observed success
add-success: PASS: Expected and observed success
Summary: 2 passed, 0 failed, 0 errored
```

For development and tests, install the test tools too:

```bash
python -m pip install -e '.[test]'
```

## Configuration

Existing configurations default to STDIO. A minimal check is:

```yaml
server:
  command: [python, examples/basic_stdio/server.py]
tool:
  name: ping
  arguments: {}
expected: success
```

`server.command` starts the local MCP server, `tool.name` selects a tool,
`arguments` supplies its JSON-compatible arguments, and `expected` is either
`success` or `tool_error`.

See [Configuration](docs/configuration.md) for multiple checks, HTTP servers,
timeouts, authentication environment variables, and validation rules.

## Results and exit codes

| Result | Meaning |
| --- | --- |
| PASS | The observed behavior matched the explicit expectation. |
| FAIL | The server responded, but the outcome or expected HTTP status differed. |
| ERROR | Configuration, setup, timeout, or transport execution failed. |

The process exits with `0` when all checks pass, `1` when at least one check
fails without execution errors, and `2` when any check errors. See
[Reporting](docs/reporting.md) for terminal output, JSON schema version 1, and
atomic report files.

## Documentation

- [Configuration guide](docs/configuration.md)
- [STDIO and Streamable HTTP transports](docs/transports.md)
- [Security testing](docs/security-testing.md)
- [Reporting and JSON schema](docs/reporting.md)
- [Architecture guide](docs/architecture.md)
- [Runnable examples](examples/)
- [Contributing](CONTRIBUTING.md)
- [Security policy](SECURITY.md)
- [Changelog](CHANGELOG.md)

## Project status

The current development version is `0.1.0`; initial release preparation is in
progress. The implemented checks are intended for repeatable local and
authorized testing, not comprehensive security auditing or compliance
certification.

## Contributing

Bug reports, focused test scenarios, and documentation improvements are
welcome. Start with [CONTRIBUTING.md](CONTRIBUTING.md) for setup, quality
checks, and fixture conventions.

## Security

Test only servers you own or are authorized to assess. STDIO YAML configurations
can execute local commands with the current user's permissions; never run an
untrusted YAML file. Keep credentials in environment variables and treat
diagnostic output carefully. Read the [security policy](SECURITY.md) and the
[security-testing guide](docs/security-testing.md) before testing protected
servers.

## License

[MIT License](LICENSE)

## Disclaimer

MCP Verdict is an independent open-source project and is not affiliated with or
endorsed by the Model Context Protocol maintainers.
