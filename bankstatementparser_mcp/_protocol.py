# Copyright (C) 2023-2026 Sebastien Rousseau.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Wire corrections the mcp 2.x SDK does not make on its own.

**Unknown resource over streamable HTTP.** On the 2026-07-28 path the
SDK picks the HTTP status from the JSON-RPC error code alone, so the
``-32602`` that ``resources/read`` returns for a URI that does not exist
(SEP-2164, with ``data.uri`` naming it) goes out as HTTP 400, the
status reserved for an envelope the server refused to read. A client
then sees a transport failure instead of the protocol answer.
:class:`UnknownResourceAsResult` sends that one reply with HTTP 200;
every other status is left as the SDK chose it.

**The handshake revision in server/discover.** Over streamable HTTP the
server still answers ``initialize`` (the 2025-11-25 handshake) beside
the stateless 2026-07-28 requests on one endpoint, as
docs/transports.md promises, but the SDK's ``server/discover`` lists
only the 2026-07-28 revisions, so a client cannot see that it may
negotiate down. :func:`advertise_handshake` adds
:data:`HANDSHAKE_REVISION` to ``supportedVersions`` there. Over stdio
the first message fixes a connection's era, so one that has sent
``server/discover`` cannot negotiate down, and its reply is left as is.

On mcp 1.x none of this applies (no 2026-07-28 path), and
:func:`install` does nothing.
"""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable, MutableMapping
from typing import Any

from bankstatementparser_mcp._mcp_compat import MCP_MAJOR

__all__ = [
    "HANDSHAKE_REVISION",
    "UnknownResourceAsResult",
    "advertise_handshake",
    "install",
]

_Message = MutableMapping[str, Any]
_Receive = Callable[[], Awaitable[_Message]]
_Send = Callable[[_Message], Awaitable[None]]
_ASGIApp = Callable[[_Message, _Receive, _Send], Awaitable[None]]

_INVALID_PARAMS = -32602

#: The initialize-handshake revision this server serves and advertises.
HANDSHAKE_REVISION = "2025-11-25"


def _is_unknown_resource(body: bytes) -> bool:
    """Whether ``body`` is the SEP-2164 unknown-resource error."""
    try:
        error = json.loads(body).get("error") or {}
    except (ValueError, AttributeError):
        return False
    data = error.get("data")
    return error.get("code") == _INVALID_PARAMS and (
        isinstance(data, dict) and "uri" in data
    )


class UnknownResourceAsResult:
    """ASGI wrapper: an unknown ``resources/read`` URI answers HTTP 200."""

    def __init__(self, app: _ASGIApp) -> None:
        self.app = app

    async def __call__(
        self, scope: _Message, receive: _Receive, send: _Send
    ) -> None:
        headers = dict(scope.get("headers") or ())
        if headers.get(b"mcp-method") != b"resources/read":
            await self.app(scope, receive, send)
            return
        held: list[_Message] = []

        async def relay(message: _Message) -> None:
            if message["type"] == "http.response.start" and (
                message["status"] == 400
            ):
                held.append(message)
                return
            if held and message["type"] == "http.response.body":
                start = held.pop()
                if _is_unknown_resource(message.get("body", b"")):
                    start = {**start, "status": 200}
                await send(start)
            await send(message)

        await self.app(scope, receive, relay)


async def advertise_handshake(
    ctx: Any, call_next: Callable[[Any], Awaitable[Any]]
) -> Any:
    """Server middleware: list the handshake revision in an HTTP discover."""
    result = await call_next(ctx)
    if ctx.method != "server/discover" or not isinstance(result, dict):
        return result
    if ctx.request is None:  # stdio: no HTTP request behind the message
        return result
    versions = result.get("supportedVersions", [])
    if HANDSHAKE_REVISION in versions:
        return result
    return {**result, "supportedVersions": [*versions, HANDSHAKE_REVISION]}


def install(server: Any) -> Any:
    """Apply the corrections to ``server`` and return it."""
    if MCP_MAJOR < 2:  # pragma: no cover  (mcp 1.x has no 2026-07-28 path)
        return server
    server.middleware.append(advertise_handshake)
    build_app = server.streamable_http_app

    def streamable_http_app(**kwargs: Any) -> UnknownResourceAsResult:
        """The SDK's streamable HTTP app, wrapped."""
        return UnknownResourceAsResult(build_app(**kwargs))

    server.streamable_http_app = streamable_http_app
    return server
