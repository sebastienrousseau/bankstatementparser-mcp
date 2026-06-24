#!/usr/bin/env python3
"""Example: call the bankstatementparser-mcp server's tools in-process.

Usage:
    pip install bankstatementparser-mcp     # requires Python 3.10+
    python examples/01_mcp_tools.py

The bankstatementparser MCP server (launched as ``bankstatementparser-mcp``
over stdio) exposes the bankstatementparser library to AI agents. This
example invokes the same tools directly, without a transport, to show what
an agent would receive.
"""

from bankstatementparser_mcp.server import (
    detect_format,
    list_supported_formats,
    parse_statement,
)

CSV = (
    "date,description,amount,currency,balance\n"
    "2023-01-02,Salary,500.00,EUR,1500.00\n"
    "2023-01-03,Groceries,-40.50,EUR,1459.50\n"
)


def main() -> None:
    """Run a small read-only walkthrough of the tools."""
    print("supported formats ->", list_supported_formats())
    print("detect_format     ->", detect_format(CSV, "statement.csv"))

    parsed = parse_statement(CSV, "statement.csv")
    print("parse_statement   ->", parsed["transaction_count"], "transactions")
    print("columns           ->", parsed["columns"])


if __name__ == "__main__":
    main()
