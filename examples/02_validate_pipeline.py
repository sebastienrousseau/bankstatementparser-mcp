#!/usr/bin/env python3
"""Example: validate then summarise a statement with the MCP tools.

Usage:
    pip install bankstatementparser-mcp     # requires Python 3.10+
    python examples/02_validate_pipeline.py

Shows how an agent would chain the tools to give a user feedback before
trusting a statement:

1. ``validate_statement`` — confirm the payload parses cleanly.
2. ``summarize_statement`` — read the opening/closing balances.
"""

from bankstatementparser_mcp.server import (
    summarize_statement,
    validate_statement,
)

CSV = (
    "date,description,amount,currency,balance\n"
    "2023-01-02,Salary,500.00,EUR,1500.00\n"
    "2023-01-03,Groceries,-40.50,EUR,1459.50\n"
)


def main() -> None:
    """Demonstrate a validate-then-summarise loop."""
    report = validate_statement(CSV, "statement.csv")
    print(
        f"is_valid={report['is_valid']} "
        f"format={report['format']} "
        f"transactions={report['transaction_count']}"
    )

    summary = summarize_statement(CSV, "statement.csv")
    print("summary ->", summary)


if __name__ == "__main__":
    main()
