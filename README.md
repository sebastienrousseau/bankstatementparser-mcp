<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

<p align="center">
  <img src="https://cloudcdn.pro/bankstatementparser/v1/logos/bankstatementparser.svg" alt="bankstatementparser-mcp logo" width="128" />
</p>

<h1 align="center">bankstatementparser-mcp</h1>

<p align="center">
  Model Context Protocol server that lets AI agents read, validate and summarise bank statements (CAMT.053, pain.001, MT940, OFX/QFX, CSV) through the bankstatementparser library.
</p>

<p align="center">
  <a href="https://github.com/sebastienrousseau/bankstatementparser-mcp/actions"><img src="https://img.shields.io/github/actions/workflow/status/sebastienrousseau/bankstatementparser-mcp/ci.yml?style=for-the-badge&logo=github" alt="Build" height="28" /></a>
  <a href="https://pypi.org/project/bankstatementparser-mcp/"><img src="https://img.shields.io/pypi/v/bankstatementparser-mcp?style=for-the-badge&color=fc8d62&logo=python" alt="Registry" height="28" /></a>
  <a href="https://sebastienrousseau.com/bankstatementparser-mcp/"><img src="https://img.shields.io/badge/docs-user%20manual-0a7bbb?style=for-the-badge&labelColor=555555&logo=materialformkdocs" alt="Docs" height="28" /></a>
  <a href="https://scorecard.dev/viewer/?uri=github.com/sebastienrousseau/bankstatementparser-mcp"><img src="https://img.shields.io/ossf-scorecard/github.com/sebastienrousseau/bankstatementparser-mcp?style=for-the-badge&label=OpenSSF%20Scorecard&logo=openssf" alt="OpenSSF Scorecard" height="28" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache--2.0%20OR%20MIT-blue.svg?style=for-the-badge" alt="License: Apache-2.0 OR MIT" height="28" /></a>
  <a href="https://github.com/sebastienrousseau/bankstatementparser-mcp/blob/main/docs/POLICIES.md"><img src="https://img.shields.io/badge/python-3.10%2B-93450a.svg?style=for-the-badge&logo=python" alt="Python 3.10+" height="28" /></a>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/sebastienrousseau/bankstatementparser-mcp/main/.github/demo.gif" alt="A terminal running bankstatementparser-mcp --version, then the 01_mcp_tools.py and 02_validate_pipeline.py examples detecting, parsing, validating and summarising inline statements" width="100%" />
</p>

---

## Contents

**Getting started**

- [Install](#install): PyPI, source, Docker (GHCR), the MCP Registry
- [Requirements](#requirements): toolchain floor, platforms
- [Quick Start](#quick-start): register the server with an MCP client

**The bankstatementparser-mcp ecosystem**

- [The bankstatementparser-mcp ecosystem](#the-bankstatementparser-mcp-ecosystem): the core library, the LSP, the ISO 20022 MCP servers

**Library reference**

- [Capabilities at a glance](#capabilities-at-a-glance): the current surface by theme
- [Ecosystem comparison](#ecosystem-comparison): short matrix; full table at [`docs/COMPARISON.md`](docs/COMPARISON.md)
- [Benchmarks](#benchmarks): headline numbers; full table at [`docs/BENCHMARKS.md`](docs/BENCHMARKS.md)
- [Features](#features): module-level capability list
- [Configuration](#configuration): core options
- [Examples](#examples): runnable example index

**Operational**

- [When not to use bankstatementparser-mcp](#when-not-to-use-bankstatementparser-mcp): limitations
- [Development](#development): make targets, fuzzing, CI
- [Security](#security): guarantees and compliance
- [Documentation](#documentation): all reference docs
- [Stability guarantees](#stability-guarantees): SemVer axis, output stability, minimum toolchain discipline
- [License](#license)

---

## Install

### As a Python library

```bash
pip install bankstatementparser-mcp
```

That installs the `bankstatementparser-mcp` command, `bankstatementparser >= 0.0.35` and the MCP SDK.

| Channel | Command | Notes |
| :--- | :--- | :--- |
| PyPI | `pip install bankstatementparser-mcp` | Add `[langchain]` for the LangChain adapter |
| Source | `git clone https://github.com/sebastienrousseau/bankstatementparser-mcp && cd bankstatementparser-mcp && poetry install` | For development |
| Docker (GHCR) | `docker pull ghcr.io/sebastienrousseau/bankstatementparser-mcp:latest` | Multi-arch (linux/amd64, linux/arm64); runs `bankstatementparser-mcp` over stdio; pass `--transport streamable-http --host 0.0.0.0` and publish port 8000 for HTTP |

An isolated virtual environment keeps the server's dependencies apart:

```sh
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows
python -m pip install -U bankstatementparser-mcp
```

### MCP Registry

The server is listed in the MCP Registry under this name, which the registry checks against this README:

`mcp-name: io.github.sebastienrousseau/bankstatementparser-mcp`

### Shell completions

Bash and zsh completions for the command line live in [`completions/`](completions/), generated from the server's own argument parser (`make completions`).

### Packaging status

[![Packaging status](https://repology.org/badge/vertical-allrepos/python:bankstatementparser-mcp.svg)](https://repology.org/project/python:bankstatementparser-mcp/versions)

Repology lists every repository that packages `bankstatementparser-mcp`. PyPI and GHCR are the channels this project publishes to itself.

---

## Requirements

- **Python 3.10 or later.** CI tests CPython 3.10, 3.11, 3.12, 3.13 and 3.14 on Linux, macOS and Windows; [`docs/POLICIES.md`](docs/POLICIES.md) says when the floor moves.
- **[`bankstatementparser`](https://pypi.org/project/bankstatementparser/) 0.0.35 or later**, the parser core every tool delegates to.
- **The MCP SDK**, `mcp >= 1.30` on the 1.x line or `>= 2.2` on 2.x (2.0 and 2.1 are excluded for GHSA-84m7-p3x7-pcfv).
- **An MCP client** (Claude Desktop, Claude Code, an IDE, or an agent framework) to launch it. The Docker image needs only a container runtime.

---

## Quick Start

```json
{
  "mcpServers": {
    "bankstatementparser": { "command": "bankstatementparser-mcp" }
  }
}
```

Add this to your MCP client's configuration (Claude Desktop shown) and restart the client: the five tools, the resource and the prompt are then available to the agent. By default the server speaks JSON-RPC over stdin/stdout, so it is meant to be launched by an MCP client, not used interactively. For a shared deployment over HTTP, see [Configuration](#configuration).

---

## The bankstatementparser-mcp ecosystem

bankstatementparser-mcp is the agent-facing layer of the `bankstatementparser` suite, whose packages ship one version together, and the multi-format ingestion server of the ISO 20022 MCP servers. Dependency ranges are kept aligned, so the servers co-install in one Python environment. The full tables are in [The suite](docs/suite.md).

| Component | Purpose | Use case |
| :--- | :--- | :--- |
| [`bankstatementparser`](https://github.com/sebastienrousseau/bankstatementparser) | The parser core: CAMT, pain.001, CSV, OFX, QFX, MT940 and PDF statements | Parsing statements from Python or the CLI |
| **`bankstatementparser-mcp`** | This server: five MCP tools, one resource, one prompt | An agent reading statements in mixed or legacy formats |
| [`bankstatementparser-lsp`](https://github.com/sebastienrousseau/bankstatementparser-lsp) | Language server with live MT940 diagnostics | Editing MT940 files |
| Loaders, writers and transport | BAI2, MT942, CFONB, CAMT.054, SEPA and BACS loaders; XLSX, QIF, OFX and SWIFT writers; EBICS transport | Formats beyond the core, and retrieval over EBICS |
| [`camt053-mcp`](https://github.com/sebastienrousseau/camt053-mcp) | ISO 20022 `camt.053`/`camt.052` statements end to end | Deep camt.05x work |
| [`reconcile-mcp`](https://github.com/sebastienrousseau/reconcile-mcp) | Matches `pain.001` payments against `camt.053` entries | Statement and payment reconciliation |

---

## Capabilities at a glance

| Area | Capability | Status |
| :--- | :--- | :--- |
| Tools | `list_supported_formats`, `detect_format`, `parse_statement`, `validate_statement`, `summarize_statement` | Shipped |
| Resource | `bankstatementparser://formats`, the supported-format catalogue | Shipped |
| Prompt | `analyze_statement`, a guided read-and-reconcile walkthrough | Shipped |
| Formats | `camt`, `pain001`, `csv`, `ofx`, `qfx`, `mt940` | Shipped |
| Transports | stdio; streamable HTTP (2026-07-28 and 2025-11-25); HTTP+SSE (2024-11-05) | Shipped |
| Adapters | LangChain, CrewAI, LlamaIndex tool objects | Shipped |
| Distribution | PyPI wheel and sdist, multi-arch GHCR image, MCP Registry entry | Shipped |

---

## Ecosystem comparison

The choice is between this server, the library it wraps, and a deeper single-format server. Every cell comes from the projects' own READMEs.

| Project | Input formats | Interface | Input model |
| :--- | :---: | :---: | :---: |
| **bankstatementparser-mcp** | CAMT.053, pain.001, MT940, OFX, QFX, CSV | MCP (stdio, streamable HTTP, SSE) | Inline content and a filename hint |
| `bankstatementparser` | The same, plus PDF | Python library and CLI | Paths on disk |
| `camt053-mcp` | `camt.053`/`camt.052` | MCP (stdio, authenticated streamable HTTP) | Tool arguments |

See [`docs/COMPARISON.md`](docs/COMPARISON.md) for the evidence and complete matrix.

---

## Benchmarks

`benches/bench_detect_and_parse.py` times `detect_format` and `parse_statement` on generated statements. Detection costs 5 to 11 ms per call whatever the size, because it peeks at the head of the document; parsing grows with the document.

| Scenario | Result | Environment |
| :--- | ---: | :--- |
| `detect_format`, CAMT.053, 2,000 entries (530 KiB) | 6.6 ms | Apple M1 Pro, macOS 27.2.1, CPython 3.12.16 |
| `parse_statement`, CAMT.053, 2,000 entries (530 KiB) | 132.8 ms | Apple M1 Pro, macOS 27.2.1, CPython 3.12.16 |
| `parse_statement`, MT940, 2,000 entries (132 KiB) | 40.7 ms | Apple M1 Pro, macOS 27.2.1, CPython 3.12.16 |
| `parse_statement`, CSV, 2,000 entries (82 KiB) | 9.4 ms | Apple M1 Pro, macOS 27.2.1, CPython 3.12.16 |

See [`docs/BENCHMARKS.md`](docs/BENCHMARKS.md) for methodology and full results.

---

## Features

- **`bankstatementparser_mcp.server`**: the MCP server. Five tools (`list_supported_formats`, `detect_format`, `parse_statement`, `validate_statement`, `summarize_statement`), one resource and one prompt. Every tool is a thin wrapper over the `bankstatementparser` parser core (`create_parser`, `detect_statement_format`), so results behave identically to the library.
- **Inline content.** An MCP client does not share the server's filesystem, so the tools take the statement text plus a filename hint and write it to a private temporary file for the duration of one call.
- **Errors as data.** `detect_format`, `parse_statement` and `summarize_statement` refuse an unparseable payload with a `ToolError` naming the filename and the parser's reason; `validate_statement` returns `{"is_valid": false, "error": ...}` instead of raising.
- **`bankstatementparser_mcp.adapters`**: the same tools as LangChain, CrewAI and LlamaIndex tool objects, each framework imported only when its adapter is called.
- **`bankstatementparser_mcp._cli` and `_transports`**: the command line shared by the suite's servers, and the stdio, streamable HTTP and SSE launchers.
- **`bankstatementparser_mcp._mcp_compat`**: one codebase on MCP SDK 1.x (`FastMCP`) and 2.x (`MCPServer`).

The tools, resource and prompt are described in full in the [manual](docs/tools.md).

---

## Configuration

The server has no configuration file and reads no environment variables. Everything is a command-line flag:

| Flag | Default | Effect |
| :--- | :--- | :--- |
| `--transport` | `stdio` | `stdio`, `streamable-http` (HTTP at `/mcp`) or `sse` (HTTP+SSE at `/sse` and `/messages/`) |
| `--host` | `127.0.0.1` | Interface the HTTP transports bind |
| `--port` | `8000` | Port the HTTP transports bind |
| `--version` | | Print the version and exit |

The HTTP transports carry no authentication of their own: bind loopback, or put the server behind a gateway you trust before binding a routable address. A client registers the HTTP endpoint with `{"mcpServers": {"bankstatementparser": {"url": "http://127.0.0.1:8000/mcp"}}}`. See [Transports](docs/transports.md) and [ADR 0001](docs/adr/0001-three-transports-one-command-line.md).

---

## Examples

The tools are plain functions on `bankstatementparser_mcp.server`, so you can call them in-process:

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

The resource and prompt are plain functions too: `formats_resource` backs `bankstatementparser://formats`, and `analyze_statement` returns the guided multi-step prompt.

```python
from bankstatementparser_mcp.server import (
    analyze_statement,
    formats_resource,
)

print(formats_resource())          # the supported-formats catalogue
print(analyze_statement("statement.csv"))  # the guided analysis prompt
```

[`examples/`](examples/) holds four runnable walkthroughs, each run in CI:

| Example | Demonstrates |
| :--- | :--- |
| [`01_mcp_tools.py`](examples/01_mcp_tools.py) | `list_supported_formats`, `detect_format` and `parse_statement` |
| [`02_validate_pipeline.py`](examples/02_validate_pipeline.py) | `validate_statement` then `summarize_statement` before trusting a statement |
| [`03_parse_bank_replies.py`](examples/03_parse_bank_replies.py) | Detecting and parsing an inline SWIFT MT940 statement |
| [`04_resource_and_prompt.py`](examples/04_resource_and_prompt.py) | The `bankstatementparser://formats` resource and the `analyze_statement` prompt |

---

## When not to use bankstatementparser-mcp

- **You're not driving an MCP-aware agent.** Use the [`bankstatementparser`](https://pypi.org/project/bankstatementparser/) CLI or library directly: it exposes the same surface with less indirection.
- **You need to parse files already on disk in bulk.** The library's CLI reads paths directly and avoids the inline-content round trip the MCP tools use.
- **You need authentication on the HTTP transports.** The server adds none; it belongs on loopback or behind a gateway you trust.
- **Your format is not one of the six.** BAI2, MT942, CFONB, CAMT.054, SEPA and BACS are read by the suite's loader packages, not by this server.

---

## Development

```bash
git clone https://github.com/sebastienrousseau/bankstatementparser-mcp.git
cd bankstatementparser-mcp
mise install
poetry install
make check
```

`make check` runs the local gates: `ruff` and `black`, `mypy --strict`, the complexity baseline (`scripts/check_complexity.py`), `pytest` with a 100% line + branch coverage floor, `interrogate` at 100% docstring coverage, and the examples. Other targets: `make fuzz` (Atheris, 60 s, Linux x86_64 with Python 3.12+), `make docs` (the MkDocs manual, `--strict`), `make completions`, `make demo` (re-renders the GIF above with VHS from `.github/demo.tape`) and `make security` (Bandit). CI adds the OS by Python matrix, the Docker build, CodeQL, `pip-audit` on the locked requirements, the Docs Lint gates, and MCP protocol conformance. [`CONTRIBUTING.md`](CONTRIBUTING.md) covers branches, commit signing and sign-off.

---

## Security

- **No persistent filesystem writes from tools.** Each call writes the inline content to a private temporary file that is deleted as soon as the call returns.
- **Validation failures** from `validate_statement` are returned as structured `{"is_valid": false, "error": ...}` payloads, never as stack traces.
- **Loopback by default.** The HTTP transports bind `127.0.0.1` unless `--host` says otherwise.
- **Fuzzing.** `fuzz/fuzz_tools.py` drives every payload-taking tool with Atheris in CI and fails on any exception other than the `ToolError` the tools promise.
- **Supply chain.** Dependencies are locked in `poetry.lock`, CI installs hash-pinned exports of it, and `pip-audit`, Bandit and CodeQL run on every change. Releases publish to PyPI through OIDC trusted publishing and carry cosign signatures, SLSA provenance and SBOMs; every workflow action is pinned by commit SHA except the SLSA generator, which must be referenced by tag.

Report vulnerabilities according to [`SECURITY.md`](SECURITY.md).

---

## Documentation

- **User manual:** [sebastienrousseau.com/bankstatementparser-mcp](https://sebastienrousseau.com/bankstatementparser-mcp/), built from [`docs/`](docs/) with MkDocs
- **API reference:** [the manual's API page](https://sebastienrousseau.com/bankstatementparser-mcp/api/), generated from the docstrings
- **Developer docs:** [`CONTRIBUTING.md`](CONTRIBUTING.md), [`ARCHITECTURE.md`](ARCHITECTURE.md), [`RELEASING.md`](RELEASING.md), [`AGENTS.md`](AGENTS.md)
- **The suite:** [`docs/suite.md`](docs/suite.md), with every `bankstatementparser` package and ISO 20022 MCP server
- **Decisions and history:** [`docs/adr/`](docs/adr/index.md), [`ROADMAP.md`](ROADMAP.md), [`CHANGELOG.md`](CHANGELOG.md)
- **Directory listing:** [Glama](https://glama.ai/mcp/servers/sebastienrousseau/bankstatementparser-mcp)
- **MCP specification:** [modelcontextprotocol.io](https://modelcontextprotocol.io)

---

## Stability guarantees

- **Versioning.** Releases stay on the `0.0.x` line and step by exactly `0.0.1`, in lockstep with the rest of the `bankstatementparser` suite. Under SemVer a `0.0.x` release may break anything; this project names each break in the CHANGELOG instead.
- **The breaking axis is the MCP surface**: tool, resource and prompt names, their arguments, and the shape of what they return. Renaming or removing any of them, or changing a returned field, is a breaking change and is called out in the CHANGELOG, even though no Python signature moves.
- **Output stability.** Parsing is deterministic: the same statement and filename hint give the same result on the same `bankstatementparser` version. A change in what a tool returns for the same input is treated as breaking.
- **Command line.** `--transport`, `--host`, `--port` and `--version` keep their names and defaults; the shell completions are regenerated from the parser so they cannot drift.
- **Minimum toolchain.** Python 3.10 is the floor; it moves only in a release, for the whole suite at once, with the reason in the CHANGELOG ([`docs/POLICIES.md`](docs/POLICIES.md)).

---

## License

Dual-licensed under [Apache License, Version 2.0](LICENSE-APACHE) or [MIT](LICENSE-MIT), at your option (`SPDX-License-Identifier: Apache-2.0 OR MIT`). Any contribution submitted for inclusion in the work shall be dual-licensed as above, without additional terms or conditions.
