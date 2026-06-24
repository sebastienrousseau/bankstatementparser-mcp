<!-- SPDX-License-Identifier: Apache-2.0 -->

# Getting support

Thanks for using bankstatementparser-mcp. Here's the fastest way to get help, by need.

## Questions & how-to

- **Read first:** the [README](README.md), the runnable
  [`examples/`](examples/) (tool walkthrough, validation pipeline,
  bank-reply parsing), and the parent
  [`bankstatementparser`](https://github.com/sebastienrousseau/bankstatementparser) repo for
  message-type / scheme background.
- **Still stuck?** Open a
  [GitHub Discussion](https://github.com/sebastienrousseau/bankstatementparser/discussions)
  on the parent repo (shared with bankstatementparser and bankstatementparser-lsp) or a question
  issue here. Include your Python version, `bankstatementparser-mcp` version
  (`python -c "import bankstatementparser_mcp; print(bankstatementparser_mcp.__version__)"`), your
  MCP client (Claude Desktop / IDE / agent), and a minimal reproducer.

## Bugs

Open a bug report at
<https://github.com/sebastienrousseau/bankstatementparser-mcp/issues/new> with a
minimal reproducer, the tool name, the arguments, and the full error
payload. A failing record set (with sensitive values redacted) helps
enormously.

## Feature requests

Open a feature request at
<https://github.com/sebastienrousseau/bankstatementparser-mcp/issues/new>. New MCP
tools, resources, and prompts on top of the
[`bankstatementparser`](https://github.com/sebastienrousseau/bankstatementparser) public API are
especially welcome — see [ARCHITECTURE.md](ARCHITECTURE.md) for the
extension points and [ROADMAP.md](ROADMAP.md) for what's planned.

## Security

**Do not** open public issues for vulnerabilities. Follow the private
disclosure process in [SECURITY.md](SECURITY.md).

## Contributing & maintaining

See [CONTRIBUTING.md](CONTRIBUTING.md) and [GOVERNANCE.md](GOVERNANCE.md).

## Supported versions

Fixes land on the latest release line. See [SECURITY.md](SECURITY.md) for
the supported-version policy. bankstatementparser-mcp requires Python 3.10+.
