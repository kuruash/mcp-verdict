"""MCP stdio fixture that never responds to initialization."""

import time


if __name__ == "__main__":
    # Stay alive long enough to exceed the client timeout, then exit naturally.
    time.sleep(5)
