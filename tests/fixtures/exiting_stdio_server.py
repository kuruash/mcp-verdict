"""MCP stdio fixture that exits before completing initialization."""

import sys


if __name__ == "__main__":
    print("fixture exited during initialization", file=sys.stderr)
    raise SystemExit(1)
