#!/usr/bin/env python3
"""Example: parse a SWIFT MT940 statement with the MCP tools.

Usage:
    pip install bankstatementparser-mcp     # requires Python 3.10+
    python examples/03_parse_bank_replies.py

Reads an inline MT940 statement, detects its format, and prints the
structured transactions plus the summary as JSON.
"""

import json

from bankstatementparser_mcp.server import detect_format, parse_statement

MT940 = (
    ":20:STARTUMS\n"
    ":25:1234567890\n"
    ":28C:00001/001\n"
    ":60F:C230101EUR1000,00\n"
    ":61:2301020102C500,00NTRFNONREF//abc\n"
    ":86:Salary payment\n"
    ":62F:C230102EUR1500,00"
)


def main() -> None:
    """Detect and parse the MT940 statement, then print the result."""
    print("detected format:", detect_format(MT940, "statement.mt940"))

    parsed = parse_statement(MT940, "statement.mt940")
    print(json.dumps(parsed, indent=2, default=str)[:600], "...")


if __name__ == "__main__":
    main()
