# Security Policy

## Reporting Security Vulnerabilities

If you discover a security vulnerability in bankstatementparser-mcp,
please email **security@bankstatementparser.com** instead of using the
issue tracker.

Please include:
1. Description of the vulnerability
2. Steps to reproduce
3. Potential impact
4. Suggested fix (if available)

We will acknowledge receipt within 48 hours and provide updates on
remediation timeline.

## Threat Model

`bankstatementparser-mcp` is a Model Context Protocol server that wraps
the [`bankstatementparser`](https://github.com/sebastienrousseau/bankstatementparser)
library and exposes it as agent tools. It runs locally over stdio (no
network listener of its own), so the security surface is:

- **Untrusted arguments** - tool calls (`parse_statement`,
  `validate_statement`, `detect_format`, `summarize_statement`) can come
  from any MCP client an agent has access to.
- **Inline content** - the tools accept the raw statement text as a
  string argument and write it to a private temporary file for the
  duration of a single call.
- **No caller-supplied paths** - the tools do not open arbitrary
  filesystem paths; only the temporary file the server itself created is
  read back.

## Hardening

- **Private temp files** - each call writes its inline content to a file
  created by `tempfile.mkstemp`, which the server removes in a `finally`
  block as soon as the call returns. No persistent artefacts remain.
- **Validation as data** - `validate_statement` returns
  `{"is_valid": false, "error": …}` rather than raising; tracebacks and
  stack frames are not surfaced over the wire.
- **No network sockets** - the server only speaks stdio. No HTTP listener
  to harden, no TLS to manage.
- **No secrets** - the package does not embed credentials or call out to
  external services.

## Continuous Integration

- `ci.yml` runs the full quality matrix (ruff, mypy, pytest with the
  100% coverage gate, interrogate).
- `security.yml` runs `bandit` against the package on every push and
  weekly via cron.
- `codeql.yml` runs GitHub's CodeQL Python analysis weekly.
- Dependency updates are picked up via Dependabot.

## Cryptography Status

`bankstatementparser-mcp` does not perform cryptographic operations. It
does not sign, encrypt, verify certificates, or hash passwords. Any
crypto-bearing package in the dependency tree is transitive via
`bankstatementparser`.

## Contact

- **Email**: security@bankstatementparser.com
- **GitHub Advisories**: https://github.com/sebastienrousseau/bankstatementparser-mcp/security/advisories
- **GitHub Discussions**: https://github.com/sebastienrousseau/bankstatementparser/discussions
