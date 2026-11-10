# Basic STDIO Server

This example is a small real MCP server that communicates over standard input
and output. It exposes two tools:

- `ping`, which returns `pong`.
- `add`, which adds two integers.

## Prerequisites

From the repository root, install MCP Verdict with its test dependencies:

```bash
python -m pip install -e '.[test]'
```

## Run with MCP Verdict

From the repository root, run the checked example configuration:

```bash
mcp-verdict check --config examples/basic_stdio/verdict.yaml
```

Expected output includes two PASS lines and:

```text
Summary: 2 passed, 0 failed
```

The configuration runs successful `ping` and `add` checks against the local
server. To connect through the Python API directly, run:

```bash
python - <<'PY'
import sys

import anyio

from mcp_verdict.stdio import connect_to_server


async def main() -> None:
    command = [sys.executable, "examples/basic_stdio/server.py"]
    async with connect_to_server(command) as connection:
        tools = await connection.session.list_tools()
        print(connection.initialize_result.protocolVersion)
        print(sorted(tool.name for tool in tools.tools))


anyio.run(main)
PY
```

The command prints a negotiated MCP protocol version and a tool list containing
`add` and `ping`. The connection context starts and stops the example server.

## Security note

`verdict.yaml` launches the command in its `server.command` field with the
current user's permissions. Run only trusted configurations; MCP Verdict does
not sandbox configured commands.
