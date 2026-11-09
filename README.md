# MCP Verdict

A lightweight, open-source testing tool for validating error handling and failure reporting in Model Context Protocol (MCP) servers.

## Why MCP Verdict?

MCP servers expose tools to AI applications. When a tool fails, the server should accurately communicate that failure so clients can respond appropriately.

Incorrect error reporting can make failed operations appear successful and complicate debugging.

MCP Verdict aims to detect these problems through reproducible tests.

## Goals

- Verify error signaling for expected MCP tool failures.
- Detect incorrectly reported successful tool results.
- Distinguish tool execution errors from protocol errors.
- Provide understandable failure reports.
- Support automated regression testing.

## Initial Scope (v0.1)

The first release will focus on validating the `isError` field in MCP tool-call results.

We will build two example MCP servers:

- A correct implementation that reports an expected execution failure using `isError: true`.
- An intentionally incorrect implementation that returns the same failure with `isError: false`.

MCP Verdict will execute both and verify the expected behavior.

## Project Status

🚧 Early development — implementation in progress.

## Roadmap

- [ ] Create example MCP servers
- [ ] Implement tool failure validation
- [ ] Add automated tests
- [ ] Build a CLI
- [ ] Add CI with GitHub Actions
- [ ] Publish v0.1.0

## Contributing

Contributions, bug reports, and suggestions are welcome.

## License

MIT License.

## Disclaimer

MCP Verdict is an independent open-source project and is not affiliated with the official Model Context Protocol project.
