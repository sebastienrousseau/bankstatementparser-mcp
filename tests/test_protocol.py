"""What passmcp checks on the wire, pinned in-process.

Each test asserts the answer passmcp scores as conforming.
"""

from __future__ import annotations

import json
from typing import Any

import anyio

import bankstatementparser_mcp.server as server

# passmcp's catalog.budget.tokens: a tool costs its wire JSON in
# characters divided by four, and 500 tokens is the ceiling per tool.
_TOKEN_CEILING = 500


def test_every_tool_fits_the_per_tool_token_budget() -> None:
    async def tools() -> list[Any]:
        return list(await server.mcp.list_tools())

    for tool in anyio.run(tools):
        wire = tool.model_dump(by_alias=True, exclude_none=True, mode="json")
        tokens = len(json.dumps(wire, separators=(",", ":"))) / 4
        assert tokens <= _TOKEN_CEILING, f"{tool.name}: {tokens} tokens"
