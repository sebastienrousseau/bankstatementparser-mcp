# Transports

One command line, three transports:

| Command | Transport | Endpoint | Protocol revisions |
| :--- | :--- | :--- | :--- |
| `bankstatementparser-mcp` | stdio | the client spawns the process | 2026-07-28, 2025-11-25 |
| `bankstatementparser-mcp --transport streamable-http` | Streamable HTTP | `http://127.0.0.1:8000/mcp` | 2026-07-28 (stateless, `server/discover`) and 2025-11-25 (`initialize`, `Mcp-Session-Id`) on the same endpoint; responses stream as server-sent events, `GET` opens the server-to-client stream |
| `bankstatementparser-mcp --transport sse` | HTTP+SSE (2024-11-05) | `http://127.0.0.1:8000/sse` and `/messages/` | for clients that still expect the older transport |

`--host` and `--port` change the bind address (defaults `127.0.0.1` and
`8000`). The HTTP transports carry no authentication of their own: bind
loopback, or put the server behind a gateway you trust before binding a
routable address. Every release is verified over streamable HTTP with
[passmcp](https://github.com/sebastienrousseau/passmcp) in both protocol
eras and over SSE with the MCP SDK client; see
[ADR 0001](adr/0001-three-transports-one-command-line.md).

Register the HTTP endpoint with a client:

```json
{
  "mcpServers": {
    "bankstatementparser": { "url": "http://127.0.0.1:8000/mcp" }
  }
}
```

By default the server speaks JSON-RPC over stdin/stdout: it is meant to
be launched by an MCP client, not used interactively.

## Shell completions

`completions/` holds bash and zsh completions for the command line,
generated from the server's own argument parser by
[shtab](https://github.com/iterative/shtab) (`make completions`). CI
regenerates them and fails if they are stale.

```bash
# bash
source completions/bankstatementparser-mcp.bash
# zsh: put the file on $fpath
cp completions/_bankstatementparser-mcp ~/.zsh/completions/
```
