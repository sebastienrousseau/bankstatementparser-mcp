# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.1] - 2026-06-24

### Added

- Initial release of `bankstatementparser-mcp`, a Model Context Protocol
  (MCP) server that exposes the
  [`bankstatementparser`](https://github.com/sebastienrousseau/bankstatementparser)
  bank statement parsing library as tools for AI agents and assistants.
- `bankstatementparser-mcp` console script that runs the FastMCP server
  over stdio.
- Five MCP tools, all delegating to the `bankstatementparser` parser
  core so they behave identically to the library:
  - `list_supported_formats` - list every bank statement format the
    parser can read (`camt`, `pain001`, `csv`, `ofx`, `qfx`, `mt940`).
  - `detect_format` - detect which statement format an inline payload is.
  - `parse_statement` - parse a statement into structured transactions
    plus a summary, with an optional row `limit`.
  - `validate_statement` - dry-run check whether a statement parses
    cleanly, returning a structured result rather than raising.
  - `summarize_statement` - return only the statement summary
    (opening/closing balances and currency).
- One resource (`bankstatementparser://formats`) describing each
  supported format and its file extensions, and one prompt
  (`analyze_statement`) guiding an agent through reading and reconciling
  a statement.
- Tools take **inline statement content** plus a filename hint and
  materialise it in a private temporary file for the duration of a
  single call, so no shared filesystem is required between client and
  server.
- **Multi-stage `Dockerfile`** - a `python:3.12-slim`-based image runs
  the server over stdio as a non-root `mcp` user
  (`docker run -i --rm bankstatementparser-mcp`).
- **Quality workflows** - `ci.yml` enforces ruff, mypy, the 100% pytest
  coverage gate, and the 100% docstring gate on Python 3.10/3.11/3.12;
  `security.yml` runs bandit + pip-audit; `codeql.yml` runs GitHub's
  CodeQL Python analysis.
- **Security policy** (`SECURITY.md`) describing the threat model and
  hardening (private temp files, no network listener, no secrets).
- `scripts/verify_versions.py` - pre-release script asserting
  `__version__`, `pyproject.toml`, and `CHANGELOG.md` agree.
- Python 3.10+ support; depends on `bankstatementparser` (>=0.0.9) and
  `mcp` (>=1.2).
- **Quality gates pinned at 100%** from the initial release:
  - `pytest --cov=bankstatementparser_mcp --cov-branch --cov-fail-under=100`
    exercising every line and branch in
    `bankstatementparser_mcp/server.py`.
  - `interrogate --fail-under=100` for module and function docstring
    coverage.

[0.0.1]: https://github.com/sebastienrousseau/bankstatementparser-mcp/releases/tag/v0.0.1
