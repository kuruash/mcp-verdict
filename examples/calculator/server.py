"""Validated arithmetic tools exposed over MCP stdio."""

from mcp.server.fastmcp import FastMCP


server = FastMCP("mcp-verdict-calculator")


@server.tool()
def add(a: float, b: float) -> float:
    """Add two numbers.

    Args:
        a: First number.
        b: Second number.

    Returns:
        The sum of ``a`` and ``b``.
    """
    return a + b


@server.tool()
def divide(a: float, b: float) -> float:
    """Divide one number by another.

    Args:
        a: Numerator.
        b: Nonzero denominator.

    Returns:
        The quotient of ``a`` and ``b``.

    Raises:
        ValueError: If ``b`` is zero.
    """
    if b == 0:
        raise ValueError("denominator must not be zero")
    return a / b


if __name__ == "__main__":
    server.run(transport="stdio")
