# The suite

bankstatementparser-mcp belongs to two families: the ISO 20022 MCP
servers, and the `bankstatementparser` packages that share one version.

## The ISO 20022 MCP Suite

`bankstatementparser-mcp` is the **ingestion layer** of eight coordinated,
vendor-neutral MCP servers that together cover the ISO 20022
bank-statement workflow and the November 2026 structured-address
cutover - statement depth, whole-catalogue routing, reconciliation,
multi-format ingestion, and address remediation. Dependency ranges are kept
aligned across the suite, so the servers co-install cleanly in a single
Python environment: start with one, add the rest as your workflow grows.

| Server | Scope | Surface | Install | Use it when |
| :--- | :--- | :--- | :--- | :--- |
| [`camt053-mcp`](https://github.com/sebastienrousseau/camt053-mcp) | ISO 20022 `camt.053`/`camt.052` bank statements: parse, validate, filter, reverse; MT940/MT942 migration; CBPR+ readiness; journal export | 24 MCP tools · 4 prompts · 3 resources | `pip install camt053-mcp` | You work with bank-to-customer statements end to end - the suite's flagship |
| [`iso20022-mcp`](https://github.com/sebastienrousseau/iso20022-mcp) | Unified gateway: `search` / `describe` / `validate` / `generate` / `parse` meta-tools routed across the `pain` · `pacs` · `camt` · `acmt` families | 7 meta-tools | `pip install "iso20022-mcp[all]"` | You want one entry point to every message family |
| [`reconcile-mcp`](https://github.com/sebastienrousseau/reconcile-mcp) | Matches expected `pain.001` payments against observed `camt.053` entries - exact, partial, one-to-many, many-to-one, every match scored and explained | 7 MCP tools | `pip install reconcile-mcp` | You need explainable statement/payment reconciliation |
| [`bankstatementparser-mcp`](index.md) | Multi-format statement ingestion: ISO 20022 CAMT.053 and pain.001, SWIFT MT940, OFX/QFX, CSV | 5 MCP tools · 1 prompt · 1 resource | `pip install bankstatementparser-mcp` | Your statements arrive in mixed or legacy formats - **this package** |
| [`structured-address-fix-mcp`](https://github.com/sebastienrousseau/structured-address-fix-mcp) | ISO 20022 postal-address classification, assessment & remediation for the November 2026 structured-address cutover, plus a high-level orchestration layer - readiness scoring, clearing-profile linting, and audit evidence (`pacs.008` / `pain.001` debtor & creditor addresses) | 9 MCP tools | `pip install structured-address-fix-mcp` | You need debtor/creditor addresses cliff-ready ahead of 14 Nov 2026 |
| [`iso20022-readiness-suite-mcp`](https://github.com/sebastienrousseau/iso20022-readiness-suite-mcp) | Orchestration gateway: detect → structurally validate → clearing-profile lint → readiness score, plus automated remediation and `pacs.002` bank-response simulation - a meta-client over the foundational servers | 4 MCP tools | `pip install iso20022-readiness-suite-mcp` | You want one high-level readiness / orchestration entry point over the suite |
| [`iso20022-bank-profile-mcp`](https://github.com/sebastienrousseau/iso20022-bank-profile-mcp) | Manages, validates and serves bank-specific clearing profiles / rule packs (CBPR+, SEPA_Instant, FedNow, Generic); premium rule-pack entitlement gating | 4 MCP tools | `pip install iso20022-bank-profile-mcp` | You lint payments against your own institution's market practice |
| [`iso20022-evidence-pack-mcp`](https://github.com/sebastienrousseau/iso20022-evidence-pack-mcp) | Compiles readiness findings, remediation diffs and simulated responses into a sealed, Ed25519-signable audit evidence pack | 6 MCP tools | `pip install iso20022-evidence-pack-mcp` | You need tamper-evident audit / certification artifacts |

In one line each: **`camt053-mcp`** is the bank-statement flagship
(deepest camt.05x surface, stdio + authenticated streamable HTTP);
**`iso20022-mcp`** is the generic message toolkit (a handful of verbs
over the whole catalogue); **`reconcile-mcp`** is the reconciliation
workflow (did the money we expected actually arrive?);
**`bankstatementparser-mcp`** is the ingestion layer (many formats in,
one transaction shape out); and **`structured-address-fix-mcp`** is the
postal-address specialist (debtor/creditor addresses cliff-ready for the
Nov 2026 cutover).

## Related MCP servers

The servers of the **ISO 20022 MCP Suite** are compared in
[the table above](#the-iso-20022-mcp-suite). The wider
family - open-source, Apache-2.0 licensed MCP servers for banking and
financial-services AI agents - also includes:

| Server | Purpose |
|---|---|
| [`pain001-mcp`](https://github.com/sebastienrousseau/pain001-mcp) | Generate & validate ISO 20022 pain.001 payment files (v03–v12, pain.008, SEPA) with rulebook checks |
| [`pacs008-mcp`](https://github.com/sebastienrousseau/pacs008-mcp) | Generate, validate, parse & scheme-check ISO 20022 pacs.008 FI-to-FI credit transfers + Nov-2026 address linting |
| [`acmt001-mcp`](https://github.com/sebastienrousseau/acmt001-mcp) | Generate & validate ISO 20022 acmt account-management messages |
| [`noyalib-mcp`](https://github.com/sebastienrousseau/noyalib) | Lossless YAML 1.2 parsing, formatting & validation (Rust, 100% spec compliance) |

## The bankstatementparser packages

`bankstatementparser` is part of a modular financial ecosystem. Optional companion packages provide specialized loaders, writers, AI agents, language servers, and transport protocol adapters:

| Package | GitHub Repository | PyPI | Role | Description |
| :--- | :--- | :--- | :--- | :--- |
| **`bankstatementparser`** | [`sebastienrousseau/bankstatementparser`](https://github.com/sebastienrousseau/bankstatementparser) | [![PyPI](https://img.shields.io/pypi/v/bankstatementparser.svg)](https://pypi.org/project/bankstatementparser/) | Core Engine | Unified parser for CAMT (052/053), PAIN.001, CSV, OFX, QFX, MT940, and PDF statements |
| **`bankstatementparser-mcp`** | [`sebastienrousseau/bankstatementparser-mcp`](https://github.com/sebastienrousseau/bankstatementparser-mcp) | [![PyPI](https://img.shields.io/pypi/v/bankstatementparser-mcp.svg)](https://pypi.org/project/bankstatementparser-mcp/) | AI Protocol | Model Context Protocol (MCP) server exposing statement tools to LLMs & AI agents |
| **`bankstatementparser-lsp`** | [`sebastienrousseau/bankstatementparser-lsp`](https://github.com/sebastienrousseau/bankstatementparser-lsp) | [![PyPI](https://img.shields.io/pypi/v/bankstatementparser-lsp.svg)](https://pypi.org/project/bankstatementparser-lsp/) | Developer Tooling | Language Server Protocol (LSP) with live SWIFT MT940 statement validation & diagnostics |
| **`bankstatementparser-transport-ebics`** | [`sebastienrousseau/bankstatementparser-transport-ebics`](https://github.com/sebastienrousseau/bankstatementparser-transport-ebics) | [![PyPI](https://img.shields.io/pypi/v/bankstatementparser-transport-ebics.svg)](https://pypi.org/project/bankstatementparser-transport-ebics/) | Transport | Automated bank statement retrieval over EBICS 3.0 (`H005`) and 2.5 (`H004`) protocols |
| **`bankstatementparser-writer-xlsx`** | [`sebastienrousseau/bankstatementparser-writer-xlsx`](https://github.com/sebastienrousseau/bankstatementparser-writer-xlsx) | [![PyPI](https://img.shields.io/pypi/v/bankstatementparser-writer-xlsx.svg)](https://pypi.org/project/bankstatementparser-writer-xlsx/) | Output Writer | Formats and exports parsed banking transactions into styled Microsoft Excel (`.xlsx`) workbooks |
| **`bankstatementparser-writer-qif`** | [`sebastienrousseau/bankstatementparser-writer-qif`](https://github.com/sebastienrousseau/bankstatementparser-writer-qif) | [![PyPI](https://img.shields.io/pypi/v/bankstatementparser-writer-qif.svg)](https://pypi.org/project/bankstatementparser-writer-qif/) | Output Writer | Serializes transactions into standard Quicken Interchange Format (`.qif`) exchange files |
| **`bankstatementparser-writer-ofx`** | [`sebastienrousseau/bankstatementparser-writer-ofx`](https://github.com/sebastienrousseau/bankstatementparser-writer-ofx) | [![PyPI](https://img.shields.io/pypi/v/bankstatementparser-writer-ofx.svg)](https://pypi.org/project/bankstatementparser-writer-ofx/) | Output Writer | Serializes transactions into standard Open Financial Exchange (`.ofx`) XML/SGML files |
| **`bankstatementparser-writer-swift`** | [`sebastienrousseau/bankstatementparser-writer-swift`](https://github.com/sebastienrousseau/bankstatementparser-writer-swift) | [![PyPI](https://img.shields.io/pypi/v/bankstatementparser-writer-swift.svg)](https://pypi.org/project/bankstatementparser-writer-swift/) | Output Writer | Exports transactions to SWIFT MT940 customer statements and MT942 interim reports |
| **`bankstatementparser-loader-bai2`** | [`sebastienrousseau/bankstatementparser-loader-bai2`](https://github.com/sebastienrousseau/bankstatementparser-loader-bai2) | [![PyPI](https://img.shields.io/pypi/v/bankstatementparser-loader-bai2.svg)](https://pypi.org/project/bankstatementparser-loader-bai2/) | Input Loader | Parses BAI2 cash-management and account balance statements |
| **`bankstatementparser-loader-mt942`** | [`sebastienrousseau/bankstatementparser-loader-mt942`](https://github.com/sebastienrousseau/bankstatementparser-loader-mt942) | [![PyPI](https://img.shields.io/pypi/v/bankstatementparser-loader-mt942.svg)](https://pypi.org/project/bankstatementparser-loader-mt942/) | Input Loader | Parses SWIFT MT942 interim transaction reports with credit/debit summary reconciliation |
| **`bankstatementparser-loader-cfonb`** | [`sebastienrousseau/bankstatementparser-loader-cfonb`](https://github.com/sebastienrousseau/bankstatementparser-loader-cfonb) | [![PyPI](https://img.shields.io/pypi/v/bankstatementparser-loader-cfonb.svg)](https://pypi.org/project/bankstatementparser-loader-cfonb/) | Input Loader | Parses French CFONB 120 / AFB120 120-byte fixed-width banking statement files |
| **`bankstatementparser-loader-camt054`** | [`sebastienrousseau/bankstatementparser-loader-camt054`](https://github.com/sebastienrousseau/bankstatementparser-loader-camt054) | [![PyPI](https://img.shields.io/pypi/v/bankstatementparser-loader-camt054.svg)](https://pypi.org/project/bankstatementparser-loader-camt054/) | Input Loader | Ingests ISO 20022 CAMT.054 real-time debit/credit notification stream XML |
| **`bankstatementparser-loader-sepa`** | [`sebastienrousseau/bankstatementparser-loader-sepa`](https://github.com/sebastienrousseau/bankstatementparser-loader-sepa) | [![PyPI](https://img.shields.io/pypi/v/bankstatementparser-loader-sepa.svg)](https://pypi.org/project/bankstatementparser-loader-sepa/) | Input Loader | Ingests ISO 20022 SEPA PAIN.002 payment status reports and PAIN.008 direct debit mandates |
| **`bankstatementparser-loader-bacs`** | [`sebastienrousseau/bankstatementparser-loader-bacs`](https://github.com/sebastienrousseau/bankstatementparser-loader-bacs) | [![PyPI](https://img.shields.io/pypi/v/bankstatementparser-loader-bacs.svg)](https://pypi.org/project/bankstatementparser-loader-bacs/) | Input Loader | Parses UK BACS Standard 18 / Faster Payments 106-byte fixed-width transmission files |
