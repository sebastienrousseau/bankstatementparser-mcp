<!-- SPDX-License-Identifier: Apache-2.0 -->

<p align="center">
  <img
    src="https://cloudcdn.pro/bankstatementparser/v1/logos/bankstatementparser.svg"
    alt="bankstatementparser-mcp logo"
    width="120"
    height="120"
  />
</p>

<h1 align="center">bankstatementparser-mcp</h1>

<p align="center">
  <b>Model Context Protocol server exposing the bankstatementparser library as first-class agent tools for reading bank statements.</b>
</p>

<p align="center">
  <a href="https://pypi.org/project/bankstatementparser-mcp/"><img src="https://img.shields.io/pypi/v/bankstatementparser-mcp?style=for-the-badge" alt="PyPI version" /></a>
  <a href="https://pypi.org/project/bankstatementparser-mcp/"><img src="https://img.shields.io/pypi/pyversions/bankstatementparser-mcp.svg?style=for-the-badge" alt="Python versions" /></a>
  <a href="https://pypi.org/project/bankstatementparser-mcp/"><img src="https://img.shields.io/pypi/dm/bankstatementparser-mcp.svg?style=for-the-badge" alt="PyPI downloads" /></a>
  <a href="https://github.com/sebastienrousseau/bankstatementparser-mcp/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/sebastienrousseau/bankstatementparser-mcp/ci.yml?branch=main&label=Tests&style=for-the-badge" alt="Tests" /></a>
  <a href="https://github.com/sebastienrousseau/bankstatementparser-mcp/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/sebastienrousseau/bankstatementparser-mcp/ci.yml?branch=main&label=Coverage&style=for-the-badge" alt="Coverage" /></a>
  <a href="#license"><img src="https://img.shields.io/pypi/l/bankstatementparser-mcp?style=for-the-badge" alt="License" /></a>
  <a href="https://glama.ai/mcp/servers/sebastienrousseau/bankstatementparser-mcp"><img src="https://glama.ai/mcp/servers/sebastienrousseau/bankstatementparser-mcp/badges/score.svg" alt="Glama MCP server score" /></a>
</p>

---

## Contents

**Getting started**

- [What is bankstatementparser-mcp?](#what-is-bankstatementparser-mcp) — the problem it solves
- [Install](#install) — PyPI, virtualenv, Docker
- [Quick start](#quick-start) — register with Claude Desktop in 30 seconds

**Library reference**

- [Tools](#tools) — the five tools, one resource, one prompt
- [Using the tools](#using-the-tools) — call them in-process from Python

**Operational**

- [When not to use bankstatementparser-mcp](#when-not-to-use-bankstatementparser-mcp) — honest boundaries
- [Development](#development) — gates, make targets
- [Security](#security) — sandboxing posture
- [Documentation](#documentation) — examples, guides
- [Contributing](#contributing) — how to get changes in
- [License](#license) — Apache-2.0

---

## What is bankstatementparser-mcp?

The [Model Context Protocol](https://modelcontextprotocol.io) (MCP) is
an open standard that lets AI agents discover and call external tools in
a uniform way. **bankstatementparser-mcp** is the MCP server that turns the
[`bankstatementparser`](https://github.com/sebastienrousseau/bankstatementparser)
library into first-class agent tools — so an assistant can read,
validate, and summarise **bank statements** in formats such as ISO 20022
CAMT.053, SWIFT MT940, OFX/QFX, and CSV directly from a conversation.

Every tool is a thin wrapper over the `bankstatementparser` parser core
(`create_parser`, `detect_statement_format`), so the results behave
identically to the CLI. Because an MCP client does not share the
server's filesystem, the tools take **inline statement content** (plus a
filename hint) and materialise it in a private temporary file for the
duration of a single call. Tools return JSON-serialisable data.

| Concern | How bankstatementparser-mcp handles it |
| :--- | :--- |
| Transport | stdio (FastMCP default); zero config beyond the client manifest |
| Input model | Inline content + filename hint; no shared filesystem required |
| Format fidelity | Tools delegate to `bankstatementparser`'s `create_parser` pipeline |
| Format detection | `detect_format` mirrors the library's `detect_statement_format` |
| Validation | `validate_statement` is a dry run that returns structured results |
| Isolation | Each call writes to a private temp file that is deleted on exit |

---

## Install

| Channel | Command | Notes |
| :--- | :--- | :--- |
| PyPI | `pip install bankstatementparser-mcp` | Pulls in `bankstatementparser >= 0.0.9` + MCP SDK |
| Source | `git clone https://github.com/sebastienrousseau/bankstatementparser-mcp && cd bankstatementparser-mcp && poetry install` | For development |
| Docker (GHCR) | `docker pull ghcr.io/sebastienrousseau/bankstatementparser-mcp:latest` | Multi-arch (linux/amd64, linux/arm64); runs `bankstatementparser-mcp` over stdio |

Requires Python 3.10 or later. Works on macOS, Linux, and Windows.

<details>
<summary>Using an isolated virtual environment (recommended)</summary>

```sh
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows
python -m pip install -U bankstatementparser-mcp
```

</details>

---

## Quick start

Register the server with any MCP client (Claude Desktop shown):

```json
{
  "mcpServers": {
    "bankstatementparser": { "command": "bankstatementparser-mcp" }
  }
}
```

That's it. Restart the client and the tools are available to the agent.

The server speaks JSON-RPC over stdin/stdout — it is meant to be
launched by an MCP client, not used interactively.

---

## Tools

All tools delegate to the `bankstatementparser` parser core, so they
behave identically to the library.

| Tool | Purpose |
| :--- | :--- |
| `list_supported_formats` | List every bank statement format the parser can read |
| `detect_format` | Detect which statement format an inline payload is |
| `parse_statement` | Parse a statement into structured transactions plus a summary |
| `validate_statement` | Dry-run check whether a statement parses cleanly |
| `summarize_statement` | Return only the statement summary (no per-transaction rows) |

Plus one resource and one prompt:

| Kind | Name | Purpose |
| :--- | :--- | :--- |
| Resource | `bankstatementparser://formats` | Read-only catalogue of supported formats and their file extensions |
| Prompt | `analyze_statement` | Guided multi-step prompt that walks an agent through reading and reconciling a statement |

Supported formats: `camt` (ISO 20022 CAMT.053, `.xml`), `pain001`
(ISO 20022 pain.001, `.xml`), `csv` (`.csv`), `ofx` (`.ofx`), `qfx`
(`.qfx`), and `mt940` (SWIFT MT940, `.mt940` / `.sta`).

---

## Using the tools

The tools are plain functions on the `bankstatementparser_mcp.server`
module, so you can call them in-process:

```python
from bankstatementparser_mcp.server import (
    detect_format,
    parse_statement,
    summarize_statement,
)

csv = (
    "date,description,amount,currency,balance\n"
    "2023-01-02,Salary,500.00,EUR,1500.00\n"
    "2023-01-03,Groceries,-40.50,EUR,1459.50\n"
)

# 1. Detect the format from the filename hint + content.
print(detect_format(csv, "statement.csv"))
# -> csv

# 2. Parse the statement into structured rows + a summary.
parsed = parse_statement(csv, "statement.csv")
print(parsed["transaction_count"], parsed["columns"])

# 3. Read just the opening/closing balances.
print(summarize_statement(csv, "statement.csv"))
```

See the [`examples/`](examples/) folder for runnable walkthroughs.

---

## When not to use bankstatementparser-mcp

- **You're not driving an MCP-aware agent.** Use the
  [`bankstatementparser`](https://pypi.org/project/bankstatementparser/)
  CLI or library directly — it exposes the same surface with less
  indirection.
- **You need to parse files already on disk in bulk.** The library's
  CLI reads paths directly and avoids the inline-content round-trip the
  MCP tools use.

---

## Development

`bankstatementparser-mcp` uses [Poetry](https://python-poetry.org/) and
[mise](https://mise.jdx.dev/).

```bash
git clone https://github.com/sebastienrousseau/bankstatementparser-mcp.git
cd bankstatementparser-mcp
mise install
poetry install
```

A `Makefile` orchestrates the quality gates (kept in lockstep with CI):

| Target | What it runs |
| :--- | :--- |
| `make check` | All gates (REQUIRED before commit) |
| `make test` | `pytest --cov=bankstatementparser_mcp --cov-branch --cov-fail-under=100` |
| `make lint` | `ruff check` + `black --check` |
| `make type-check` | `mypy --strict` |
| `make docs` | `interrogate --fail-under=100` (docstring coverage) |

Current state (v0.0.1): **100% line + branch coverage** against a 100%
enforced floor, mypy `--strict` clean, interrogate 100%.

---

## Security

- **No persistent filesystem writes from tools.** Each call writes the
  inline content to a private temporary file that is deleted as soon as
  the call returns.
- **Validation failures** from `validate_statement` are returned as
  structured `{"is_valid": false, "error": ...}` payloads — never as
  stack traces.
- **Dependencies** are pinned via `poetry.lock` and audited by
  `pip-audit` and Bandit in CI.

To report a vulnerability, please use
[GitHub private vulnerability reporting](https://github.com/sebastienrousseau/bankstatementparser-mcp/security)
rather than a public issue.

---

## Documentation

- **Runnable examples:** [`examples/`](https://github.com/sebastienrousseau/bankstatementparser-mcp/tree/main/examples)
- **Release history:** [CHANGELOG.md](https://github.com/sebastienrousseau/bankstatementparser-mcp/blob/main/CHANGELOG.md)
- **MCP specification:** [modelcontextprotocol.io](https://modelcontextprotocol.io)

---

## Contributing

Contributions are welcome — see the
[contributing instructions](https://github.com/sebastienrousseau/bankstatementparser-mcp/blob/main/CONTRIBUTING.md).
Thanks to all the
[contributors](https://github.com/sebastienrousseau/bankstatementparser-mcp/graphs/contributors)
who have helped build `bankstatementparser-mcp`.

---

## License

Licensed under the [Apache License, Version 2.0](https://opensource.org/license/apache-2-0/).
Any contribution submitted for inclusion shall be licensed as above,
without additional terms.

---

<p align="center">
  <a href="https://bankstatementparser.com">bankstatementparser.com</a> ·
  <a href="https://pypi.org/project/bankstatementparser-mcp/">PyPI</a> ·
  <a href="https://github.com/sebastienrousseau/bankstatementparser-mcp">GitHub</a>
</p>
