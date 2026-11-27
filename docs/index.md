# bankstatementparser-mcp

The [Model Context Protocol](https://modelcontextprotocol.io) (MCP) is
an open standard that lets AI agents discover and call external tools in
a uniform way. **bankstatementparser-mcp** is the MCP server that turns the
[`bankstatementparser`](https://github.com/sebastienrousseau/bankstatementparser)
library into agent tools, so an assistant can read, validate, and
summarise bank statements in formats such as ISO 20022 CAMT.053, SWIFT
MT940, OFX/QFX, and CSV directly from a conversation.

Every tool is a thin wrapper over the `bankstatementparser` parser core
(`create_parser`, `detect_statement_format`), so the results behave
identically to the CLI. Because an MCP client does not share the
server's filesystem, the tools take **inline statement content** (plus a
filename hint) and materialise it in a private temporary file for the
duration of a single call. Tools return JSON-serialisable data.

| Concern | How bankstatementparser-mcp handles it |
| :--- | :--- |
| Transport | stdio by default; `--transport streamable-http` (2026-07-28 and 2025-11-25 on one endpoint) or `--transport sse` for HTTP |
| Input model | Inline content + filename hint; no shared filesystem required |
| Format fidelity | Tools delegate to `bankstatementparser`'s `create_parser` pipeline |
| Format detection | `detect_format` mirrors the library's `detect_statement_format` |
| Validation | `validate_statement` is a dry run that returns structured results |
| Isolation | Each call writes to a private temp file that is deleted on exit |

## In this manual

- [Tools](tools.md): the five tools, the resource and the prompt.
- [Transports](transports.md): stdio, streamable HTTP and SSE.
- [The suite](suite.md): the ISO 20022 MCP servers and the
  `bankstatementparser` packages this server sits beside.
- [Comparison](COMPARISON.md) and [Benchmarks](BENCHMARKS.md).
- [Supported Python policy](POLICIES.md).
- [API reference](api.md): the importable Python surface.
- [Architecture decisions](adr/index.md), [Roadmap](roadmap.md),
  [Changelog](changelog.md) and [Security policy](security.md).

The source, issues and releases live on
[GitHub](https://github.com/sebastienrousseau/bankstatementparser-mcp);
the package is on [PyPI](https://pypi.org/project/bankstatementparser-mcp/).
