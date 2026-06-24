#!/usr/bin/env python3
"""Example: read the formats resource and the analyze_statement prompt.

Usage:
    pip install bankstatementparser-mcp     # requires Python 3.10+
    python examples/04_resource_and_prompt.py

Beyond the tools, the server exposes one MCP resource and one MCP
prompt. This example reads both directly, the same way an MCP client
would after discovering them:

1. ``formats_resource`` (``bankstatementparser://formats``) — a
   read-only catalogue of the supported input formats.
2. ``analyze_statement`` — a guided prompt that walks an agent through
   detecting, validating, parsing, and reconciling a statement.
"""

from bankstatementparser_mcp.server import (
    analyze_statement,
    formats_resource,
)


def main() -> None:
    """Print the formats catalogue and the guided analysis prompt."""
    print("resource bankstatementparser://formats ->")
    print(formats_resource())

    print()
    print("prompt analyze_statement('statement.csv') ->")
    print(analyze_statement("statement.csv"))


if __name__ == "__main__":
    main()
