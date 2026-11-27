# Comparison

Where bankstatementparser-mcp fits next to the tools a reader would
otherwise reach for. Every cell comes from this repository's README or
the linked project's own README; nothing here is a measured ranking.

| Project | Input formats | Interface | Input model |
| :--- | :--- | :--- | :--- |
| **bankstatementparser-mcp** | CAMT.053, pain.001, MT940, OFX, QFX, CSV | MCP tools (stdio, streamable HTTP, SSE) | Inline content plus a filename hint |
| [`bankstatementparser`](https://github.com/sebastienrousseau/bankstatementparser) | The same formats, plus PDF | Python library and CLI | Paths on disk |
| [`camt053-mcp`](https://github.com/sebastienrousseau/camt053-mcp) | `camt.053`/`camt.052`, MT940/MT942 migration | MCP tools (stdio, authenticated streamable HTTP) | MCP tool arguments |
| [`bankstatementparser-lsp`](https://github.com/sebastienrousseau/bankstatementparser-lsp) | MT940 | Language Server Protocol | The editor's open document |

## When each fits

- **bankstatementparser-mcp**: an MCP-aware agent has to read
  statements in mixed or legacy formats, and does not share a
  filesystem with the server.
- **bankstatementparser**: you are writing Python, or parsing files
  already on disk in bulk; it avoids the inline-content round trip.
- **camt053-mcp**: you work with ISO 20022 bank-to-customer statements
  end to end and need its deeper `camt.05x` surface.
- **bankstatementparser-lsp**: you want MT940 diagnostics while editing.

The wider family is listed in [The suite](suite.md).
