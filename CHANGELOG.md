# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.12] - 2026-06-25

### Changed

- **Audit pass.** Covered `main()` (removed a `# pragma: no cover` that masked testable code) and hardened the example-regression discovery to a set-equality check.

## [0.0.11] - 2026-06-24

### Added

- **End-to-end install smoke test** - a new `smoke` job in `ci.yml`
  ("Smoke test (installed wheel)") builds the wheel, installs it into a
  clean virtual environment (pulling `bankstatementparser` and `mcp`
  from PyPI), then imports the **installed** package and runs an example
  from a neutral working directory so the source tree is not on
  `sys.path`. This catches packaging and CI-vs-local divergence.
- **Expanded edge-case tests** keeping the 100% line + branch coverage
  honest: garbage/malformed payloads across the detect/parse/validate
  paths, the `limit` parameter at its boundaries (`0` and larger than
  the row count), an explicit-but-wrong `format`, and confirmation that
  `validate_statement` returns a structured `{"is_valid": false, ...}`
  error rather than raising.

### Changed

- **Pruned over-scaffolding CI** - removed the `nightly.yml` and
  `docs.yml` workflows (redundant for a small thin-adapter package);
  the kept workflows (`ci.yml`, `pr.yml`, `codeql.yml`, `security.yml`,
  `release.yml`, `docker.yml`) already cover the full quality posture.

## [0.0.10] - 2026-06-24

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
- **Runnable examples** under `examples/` covering every tool, the
  `bankstatementparser://formats` resource (`formats_resource`), and the
  `analyze_statement` prompt — each self-contained (inline fixtures, no
  network) and exercised by the test suite.
- **Documentation regression suite** keeping the docs honest:
  - `tests/test_docs_accuracy.py` asserts the README, CHANGELOG, and
    `examples/README.md` match the live tool/resource/prompt registry,
    the package version, and the supported-format set.
  - `tests/test_regression_examples.py` runs every `examples/*.py` as a
    subprocess and asserts a clean exit.
  - `tests/test_regression_docs.py` executes every fenced ``python``
    block in the README (and `docs/*.md`) so no documented example can
    silently rot.

[0.0.11]: https://github.com/sebastienrousseau/bankstatementparser-mcp/releases/tag/v0.0.11
[0.0.10]: https://github.com/sebastienrousseau/bankstatementparser-mcp/releases/tag/v0.0.10
