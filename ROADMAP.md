# bankstatementparser-mcp Roadmap

This roadmap tracks the next set of capabilities for the MCP companion of
the [bankstatementparser](https://github.com/sebastienrousseau/bankstatementparser)
library. The versions are **target** windows; releases ship when the
gates pass, not on a calendar.

## v0.0.1 - Initial release (current)

- Five MCP tools mirroring the bankstatementparser parser core
  (format discovery, format detection, parsing, validation, summary).
- One resource (`bankstatementparser://formats`) and one prompt
  (`analyze_statement`).
- 100% line+branch coverage gate, 100% docstring coverage gate.

## v0.0.2 - Richer output surface

- Optional structured-output schemas so MCP clients can introspect the
  transaction and summary payload shapes.
- A `reconcile_statement` tool that checks the transaction total against
  the opening/closing balances and flags discrepancies.
- Pagination cursors for very large statements instead of a flat
  `limit`.

## v0.1.0 - Hardened agent surface

- Configurable payload-size limits so a deployment can cap how much
  inline content a single call may materialise.
- Per-format streaming responses for large statements.
- Opt-in metrics tool reporting rolling counters an agent can use to
  back off under pressure.

## Out of scope (handled elsewhere)

- **Bulk path-based parsing** - use the core
  [`bankstatementparser`](https://github.com/sebastienrousseau/bankstatementparser)
  CLI, which reads files on disk directly.
