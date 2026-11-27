<!-- SPDX-License-Identifier: Apache-2.0 -->

# bankstatementparser-mcp Architecture

A map of the codebase for new contributors and maintainers. The goal is
that anyone can navigate, extend, and reason about
bankstatementparser-mcp without prior context.

## The pipeline

```text
MCP client (Claude Desktop, IDE, agent)
        |  stdio (JSON-RPC), or streamable HTTP / SSE with --transport
        v
bankstatementparser_mcp/server.py   (FastMCP server: tools, resource, prompt)
        |  inline content -> private temp file
        v
bankstatementparser parser core     (bankstatementparser.additional_parsers
        |                            .create_parser,
        |                            .detect_statement_format)
        v
structured transactions + summary
```

Tools are deliberately thin: every one is a small adapter that
materialises the inline statement content in a private temporary file,
delegates to the
[`bankstatementparser`](https://github.com/sebastienrousseau/bankstatementparser)
library, and returns a JSON-serialisable result. Because an MCP client
does not share the server's filesystem, the tools accept the raw
statement text plus a filename hint rather than a path.

## Module map

| Area | Module | Responsibility |
| :--- | :--- | :--- |
| **Server** | `bankstatementparser_mcp/server.py` | The FastMCP server, all tool / resource / prompt registrations and the temp-file helpers |
| **Entry point** | `bankstatementparser_mcp.server:main` (console script: `bankstatementparser-mcp`) | Launches the server over stdio, or over streamable HTTP / SSE with `--transport` (`_cli.py` + `_transports.py`, ADR 0001) |
| **SDK shim** | `bankstatementparser_mcp/_mcp_compat.py` | Builds the server object on mcp 2.x (`MCPServer`) or mcp 1.x (`FastMCP`) so one codebase runs on both majors |
| **Command line** | `bankstatementparser_mcp/_cli.py`, `bankstatementparser_mcp/_transports.py` | The suite's shared parser (`build_parser`, `serve`) and the transport launcher |
| **Completions** | `bankstatementparser_mcp/completion.py`, `completions/` | The console script's parser for shtab; `make completions` writes the bash and zsh files, CI fails if they are stale |
| **Adapters** | `bankstatementparser_mcp/adapters.py` | The same tools for LangChain, CrewAI and LlamaIndex, imported lazily |
| **Version** | `bankstatementparser_mcp/__init__.py` | `__version__`, kept equal to `pyproject.toml` |
| **Tests** | `tests/` | In-process regressions covering every tool, helper, the resource and the prompt; the command line; the SDK shim; docs and examples accuracy; release notes; fuzz harness smoke; and the shared suite conformance gate |
| **Fuzzing** | `fuzz/fuzz_tools.py` | Atheris target for every payload-taking tool, run by the CI `Fuzz` job |
| **Examples** | `examples/` | One runnable script per usage shape |
| **Manual** | `mkdocs.yml`, `docs/` | The MkDocs Material user manual and API reference, deployed to GitHub Pages |
| **Release helpers** | `scripts/` | `verify_versions.py` (every version restatement agrees), `release_notes.py` (release body), `export_locked_requirements.py` (hashed exports of `poetry.lock`), `check_complexity.py` (complexity baseline), `check_suite_consistency.py` (published suite agrees), `readme-check.sh` (README template) |

## Tools, resource, prompt

The current MCP surface:

- **Tools** - `list_supported_formats`, `detect_format`,
  `parse_statement`, `validate_statement`, `summarize_statement`.
- **Resource** - `bankstatementparser://formats` (a human-readable
  catalogue of the supported formats and their file extensions).
- **Prompt** - `analyze_statement(filename=...)` (guided instruction
  template for reading and reconciling a statement).

## Key design decisions

- **Delegation, not duplication.** Every tool is a thin wrapper over the
  `bankstatementparser` `create_parser` pipeline. If you want a new
  format, add it upstream rather than re-implementing parsing here.
- **Inline content, private temp files.** A closed-then-reopened temp
  file (via `tempfile.mkstemp`) is used so the file-based parsers can
  reopen the path by name; it is deleted as soon as the call returns.
- **Validation as data.** `validate_statement` never raises: a failure
  is returned as `{"is_valid": false, "error": ...}` so the agent can
  reason about failure without parsing tracebacks.
- **Loopback by default.** stdio needs no socket. The HTTP transports
  (`--transport streamable-http`, `--transport sse`) bind `127.0.0.1`
  unless `--host` says otherwise and add no authentication of their
  own; a routable deployment sits behind a gateway the operator trusts
  (ADR 0001).
- **Coverage enforced at 100%** line+branch and docstring; only the
  process entry point is `# pragma: no cover`.

## Extension points

- **Add a tool:** add an `@mcp.tool()`-decorated function in
  `bankstatementparser_mcp/server.py`; pair it with tests in
  `tests/test_mcp_server.py`.
- **Add a resource:** `@mcp.resource("bankstatementparser://...")`
  decorator.
- **Add a prompt:** `@mcp.prompt()` decorator.
- **Match a new `bankstatementparser` format:** when a new parser lands
  upstream, surface it via `_FORMAT_SUFFIX` and the format catalogue.

## Where to look first

- Runnable examples: [`examples/`](examples/)
- Decisions: [`docs/adr/`](docs/adr/index.md)
- Roadmap: [`ROADMAP.md`](ROADMAP.md)
- Release process: [`RELEASING.md`](RELEASING.md)
- Parent library: [`bankstatementparser`](https://github.com/sebastienrousseau/bankstatementparser)
