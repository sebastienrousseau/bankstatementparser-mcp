# bankstatementparser-mcp Roadmap

This roadmap tracks what is planned for the MCP companion of the
[bankstatementparser](https://github.com/sebastienrousseau/bankstatementparser)
library. It summarises the CHANGELOG and the open issues; it does not
promise work that is not tracked there. Releases ship when the gates
pass, not on a calendar.

## v0.0.19 (current)

- Five tools over the `bankstatementparser` parser core:
  `list_supported_formats`, `detect_format`, `parse_statement`,
  `validate_statement`, `summarize_statement`, all taking the statement
  text inline.
- One resource (`bankstatementparser://formats`) and one prompt
  (`analyze_statement`).
- Agent adapters for LangChain, CrewAI and LlamaIndex (`adapters.py`).
- 100% line+branch coverage gate, the shared suite conformance test, a
  detect-and-parse benchmark, and a scheduled check that the published
  suite agrees with itself.
- One version number across the `bankstatementparser` packages.

## Next release (on `main`, unreleased)

- stdio, streamable HTTP (2026-07-28 and 2025-11-25) and SSE from one
  command line (ADR 0001).
- `detect_format`, `parse_statement` and `summarize_statement` refuse an
  unparseable payload with a `ToolError` that names the caller's
  filename and the parser's reason.

## Beyond

No further work is scheduled. There are no open feature issues at the
time of writing. New formats follow the library: when a parser lands in
`bankstatementparser`, it is surfaced here through `_FORMAT_SUFFIX` and
the format catalogue in the same release window.

## Out of scope (handled elsewhere)

- **Bulk path-based parsing** - use the core
  [`bankstatementparser`](https://github.com/sebastienrousseau/bankstatementparser)
  CLI, which reads files on disk directly.
- **Editor features** - see
  [`bankstatementparser-lsp`](https://github.com/sebastienrousseau/bankstatementparser-lsp).
