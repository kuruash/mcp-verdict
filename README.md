# MCP Verdict

**Test how your MCP servers behave when things go wrong.**

MCP Verdict is an open-source developer tool for testing the security boundaries and failure-handling behavior of Model Context Protocol (MCP) servers.

The project aims to help developers catch incorrect error reporting, unexpected authorization behavior, and regressions before deploying MCP servers to production.

## Why MCP Verdict?

MCP servers connect AI applications to tools, APIs, databases, and external services.

When an MCP server receives an invalid request, encounters a tool execution failure, or receives an unauthorized request, it must respond according to its defined behavior and applicable protocol requirements.

Incorrect behavior can lead to confusing errors, security weaknesses, and unreliable AI applications.

MCP Verdict aims to make these failure scenarios reproducible and testable.

## Planned Features

### Error-Handling Tests

- Verify expected tool execution errors.
- Distinguish successful results, tool errors, and protocol errors.
- Check incorrect or missing error indicators.
- Detect regressions in error-handling behavior.

### Security Tests

- Verify that declared protected operations reject unauthenticated requests.
- Test invalid authentication credentials.
- Test authorization boundaries using explicitly configured test identities.
- Check applicable MCP authorization requirements.

### Developer Experience

- Command-line interface.
- Configurable test scenarios.
- Human-readable and JSON test reports.
- Automated testing and CI integration.

## Project Status

**Early development — pre-release.**

The project is not yet a production-ready MCP security scanner or compliance certification tool.

## Initial Milestone

Build an installable Python CLI that:

1. Connects to a real local MCP server.
2. Discovers and calls a tool.
3. Distinguishes success from tool execution failure.
4. Returns a meaningful test result and process exit code.
5. Runs automated unit and integration tests.

Security tests will follow once the shared MCP connection and test runner are reliable.

## Roadmap

- [ ] Installable Python package and CLI
- [ ] Real MCP stdio integration
- [ ] Tool error assertions
- [ ] Test configuration support
- [ ] Human-readable and JSON reports
- [ ] HTTP MCP integration
- [ ] Authentication enforcement tests
- [ ] GitHub Actions CI
- [ ] Contributor documentation

## Security

Only test MCP servers you own or are authorized to assess. Use isolated environments and test credentials. Some future checks may invoke tools with side effects.

Treat every YAML configuration as executable input. The `server.command` field
launches a local executable with the permissions of the current user. Do not
run MCP Verdict with untrusted configuration files; MCP Verdict intentionally
does not sandbox or restrict legitimate server commands.

## Contributing

Contributions, bug reports, reproducible failure scenarios, and documentation improvements are welcome.

Contribution guidelines will be added as the project matures.

## License

MIT License.

## Disclaimer

MCP Verdict is an independent open-source project and is not affiliated with or endorsed by the Model Context Protocol maintainers.
