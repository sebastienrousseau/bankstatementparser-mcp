# Tools, resource and prompt

All tools delegate to the `bankstatementparser` parser core, so they
behave identically to the library.

| Tool | What it does |
| :--- | :--- |
| `list_supported_formats` | List every bank statement format the parser can read |
| `detect_format` | Detect which statement format an inline payload is |
| `parse_statement` | Parse a statement into structured transactions plus a summary |
| `validate_statement` | Dry-run check whether a statement parses cleanly |
| `summarize_statement` | Return only the statement summary (no per-transaction rows) |

Plus one resource and one prompt:

- Resource `bankstatementparser://formats`: read-only catalogue of
  supported formats and their file extensions.
- Prompt `analyze_statement`: guided multi-step prompt that walks an
  agent through reading and reconciling a statement.

Supported formats: `camt` (ISO 20022 CAMT.053, `.xml`), `pain001`
(ISO 20022 pain.001, `.xml`), `csv` (`.csv`), `ofx` (`.ofx`), `qfx`
(`.qfx`), and `mt940` (SWIFT MT940, `.mt940` / `.sta`).

## Errors

`detect_format`, `parse_statement` and `summarize_statement` refuse an
unparseable payload with a `ToolError` that names the caller's filename
and the parser's reason. `validate_statement` never raises: a failure is
returned as `{"is_valid": false, "error": ...}` so an agent can reason
about it without parsing a traceback.

## Calling the tools in-process

The tools, the resource (`formats_resource`) and the prompt
(`analyze_statement`) are plain functions on
`bankstatementparser_mcp.server`. The README's Quick Start and Examples
show them called on an inline CSV statement, and
[`examples/`](https://github.com/sebastienrousseau/bankstatementparser-mcp/tree/main/examples)
holds four runnable walkthroughs.

## Agent framework adapters

`bankstatementparser_mcp.adapters` exposes the same tools to LangChain,
CrewAI and LlamaIndex without making those packages dependencies: each
adapter imports its framework only when called. Install the LangChain
extra with `pip install "bankstatementparser-mcp[langchain]"`.
