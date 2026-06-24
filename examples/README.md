# bankstatementparser-mcp examples

Runnable, self-contained examples for the bankstatementparser MCP server.
Run any of them from the repository root:

```sh
python examples/<name>.py
```

| Example | Demonstrates |
|---------|--------------|
| [`01_mcp_tools.py`](01_mcp_tools.py) | Calling the MCP tools in-process — `list_supported_formats`, `detect_format`, and `parse_statement` |
| [`02_validate_pipeline.py`](02_validate_pipeline.py) | Chaining `validate_statement` and `summarize_statement` to vet a statement before trusting it |
| [`03_parse_bank_replies.py`](03_parse_bank_replies.py) | Detecting and parsing an inline SWIFT MT940 statement via the MCP tools |

The examples import directly from `bankstatementparser_mcp.server`, so
install this package (and the core `bankstatementparser` library it
depends on) first:

```sh
pip install bankstatementparser-mcp   # Python 3.10+
```
