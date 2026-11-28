"""What passmcp checks on the wire, pinned in-process.

Each test sends the request passmcp sends and asserts the answer it
scores as conforming: the per-tool catalogue budget and an unknown
resource over streamable HTTP. The HTTP tests drive the server's own
ASGI app with its lifespan running, so no port is opened.
"""

from __future__ import annotations

import json
from typing import Any

import anyio
import pytest

import bankstatementparser_mcp.server as server
from bankstatementparser_mcp import _protocol
from bankstatementparser_mcp._mcp_compat import MCP_MAJOR

modern_only = pytest.mark.skipif(
    MCP_MAJOR < 2, reason="the 2026-07-28 HTTP path is 2.x"
)

# passmcp's catalog.budget.tokens: a tool costs its wire JSON in
# characters divided by four, and 500 tokens is the ceiling per tool.
_TOKEN_CEILING = 500

_META = {
    "io.modelcontextprotocol/clientCapabilities": {},
    "io.modelcontextprotocol/clientInfo": {"name": "test", "version": "0"},
    "io.modelcontextprotocol/protocolVersion": "2026-07-28",
}


def test_every_tool_fits_the_per_tool_token_budget() -> None:
    async def tools() -> list[Any]:
        return list(await server.mcp.list_tools())

    for tool in anyio.run(tools):
        wire = tool.model_dump(by_alias=True, exclude_none=True, mode="json")
        tokens = len(json.dumps(wire, separators=(",", ":"))) / 4
        assert tokens <= _TOKEN_CEILING, f"{tool.name}: {tokens} tokens"


async def _post(
    method: str, params: dict[str, Any], headers: dict[str, str]
) -> tuple[int, dict[str, Any]]:
    """POST one 2026-07-28 request to the server's streamable HTTP app."""
    app = server.mcp.streamable_http_app(streamable_http_path="/mcp")
    body = json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    ).encode()
    sent: list[dict[str, Any]] = []
    raw = {
        "host": "127.0.0.1:8000",
        "accept": "application/json, text/event-stream",
        "content-type": "application/json",
        "mcp-method": method,
        "mcp-protocol-version": "2026-07-28",
        **headers,
    }
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/mcp",
        "raw_path": b"/mcp",
        "query_string": b"",
        "root_path": "",
        "server": ("127.0.0.1", 8000),
        "client": ("127.0.0.1", 50000),
        "headers": [(k.encode(), v.encode()) for k, v in raw.items()],
    }
    delivered = False

    async def receive() -> dict[str, Any]:
        nonlocal delivered
        if delivered:
            await anyio.sleep_forever()
        delivered = True
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(message: dict[str, Any]) -> None:
        sent.append(message)

    inner = getattr(app, "app", app)
    async with inner.router.lifespan_context(inner):
        await app(scope, receive, send)
    status = next(
        m["status"] for m in sent if m["type"] == "http.response.start"
    )
    payload = b"".join(
        m.get("body", b"") for m in sent if m["type"] == "http.response.body"
    )
    return status, json.loads(payload)


@modern_only
def test_unknown_resource_is_a_jsonrpc_error_in_a_200() -> None:
    uri = "passmcp://no-such-resource"
    status, reply = anyio.run(
        _post,
        "resources/read",
        {"_meta": _META, "uri": uri},
        {"mcp-name": uri},
    )
    assert status == 200
    assert reply["error"]["code"] == -32602
    assert reply["error"]["data"] == {"uri": uri}


@modern_only
def test_a_rejected_envelope_keeps_its_400() -> None:
    uri = "bankstatementparser://formats"
    status, reply = anyio.run(
        _post,
        "resources/read",
        {"_meta": _META, "uri": uri},
        {"mcp-name": uri, "mcp-protocol-version": "1999-01-01"},
    )
    assert status == 400
    assert "error" in reply


@modern_only
def test_a_known_resource_still_reads() -> None:
    uri = "bankstatementparser://formats"
    status, reply = anyio.run(
        _post,
        "resources/read",
        {"_meta": _META, "uri": uri},
        {"mcp-name": uri},
    )
    assert status == 200
    assert reply["result"]["contents"][0]["uri"] == uri


@modern_only
def test_other_methods_pass_through_untouched() -> None:
    status, reply = anyio.run(_post, "tools/list", {"_meta": _META}, {})
    assert status == 200
    assert len(reply["result"]["tools"]) == 5


@pytest.mark.parametrize("body", [b"Bad Request", b"[]", b"{}"])
def test_a_body_that_is_not_the_unknown_resource_error(body: bytes) -> None:
    assert not _protocol._is_unknown_resource(body)
