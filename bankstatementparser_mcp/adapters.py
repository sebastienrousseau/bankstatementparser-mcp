# Copyright (C) 2023-2026 Bank Statement Parser. All rights reserved.
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

"""Framework adapters: expose the BankStatementParser tools to agent frameworks.

The server registers its tools (``list_supported_formats``, ``detect_format``,
``parse_statement``, ``validate_statement``, ``summarize_statement``) with
FastMCP. Agent frameworks such as LangChain, CrewAI and LlamaIndex each have
their own tool object; this module introspects the FastMCP tool registry and
wraps every registered tool into the requested framework's native tool type,
one framework tool per server tool.

Each ``as_*_tools`` function pulls its framework in lazily, so importing this
module -- and the base ``bankstatementparser-mcp`` install -- never depends on
any agent framework. A framework is only needed when its adapter is actually
called; if it is absent the adapter raises :class:`ImportError` naming the
extra to install (e.g. ``pip install bankstatementparser-mcp[langchain]``).

The tool metadata (name, description and the JSON ``inputSchema``) and the
underlying callable are read from the FastMCP tool registry via
:func:`_gateway_tools`. The introspected JSON input schema is passed straight
through to each framework's schema argument.
"""

from collections.abc import Callable
from typing import Any, cast

from bankstatementparser_mcp.server import mcp


def _gateway_tools() -> list[Any]:
    """Return the server's registered FastMCP / MCPServer tools for adapter wrapping.

    Reads the tool manager or server registry, so each entry carries the
    tool's ``name``, ``description``, JSON input schema (``parameters``) and
    the underlying callable (``fn``).
    """
    tm = getattr(mcp, "_tool_manager", None)
    if tm is not None and hasattr(tm, "list_tools"):
        return list(tm.list_tools())
    tools = getattr(mcp, "_tools", None)
    if tools is not None:
        return list(tools.values()) if isinstance(tools, dict) else list(tools)
    return []


def _wrap_with_tool_exception(
    fn: Callable[..., Any], tool_exception: type[Exception]
) -> Callable[..., Any]:
    """Wrap a server callable so raised errors become ``tool_exception``.

    LangChain signals a recoverable tool failure by raising
    ``ToolException``; the server tools normally return a JSON-serialisable
    payload rather than raising, but any unexpected error is mapped to the
    framework's convention here.
    """

    def _call(**kwargs: Any) -> Any:
        """Invoke the wrapped tool, mapping failures to ``tool_exception``."""
        try:
            return fn(**kwargs)
        except Exception as exc:
            raise tool_exception(str(exc)) from exc

    return _call


def _tool_func(tool: Any) -> Callable[..., Any]:
    """Extract underlying callable from tool object."""
    fn: Any = getattr(tool, "fn", getattr(tool, "func", tool))
    return cast(Callable[..., Any], fn)


def _tool_name(tool: Any) -> str:
    """Extract name attribute from tool object."""
    return getattr(tool, "name", "")


def _tool_desc(tool: Any) -> str:
    """Extract description attribute from tool object."""
    return getattr(tool, "description", "") or ""


def _tool_schema(tool: Any) -> Any:
    """Extract parameters or input schema from tool object."""
    return getattr(
        tool,
        "parameters",
        getattr(tool, "input_schema", getattr(tool, "args_schema", None)),
    )


def as_langchain_tools() -> list[Any]:
    """Wrap every server tool as a LangChain ``StructuredTool``.

    Returns one :class:`langchain_core.tools.StructuredTool` per registered
    server tool, carrying its name, description and JSON input schema; the
    callable is wrapped so raised errors surface as ``ToolException``.

    Raises:
        ImportError: if ``langchain-core`` is not installed
            (``pip install bankstatementparser-mcp[langchain]``).
    """
    try:
        from langchain_core.tools import StructuredTool, ToolException
    except ImportError as exc:
        raise ImportError(
            "LangChain is not installed. Install it with "
            "`pip install bankstatementparser-mcp[langchain]`."
        ) from exc

    return [
        StructuredTool.from_function(
            func=_wrap_with_tool_exception(_tool_func(tool), ToolException),
            name=_tool_name(tool),
            description=_tool_desc(tool),
            args_schema=_tool_schema(tool),
        )
        for tool in _gateway_tools()
    ]


def as_crewai_tools() -> list[Any]:
    """Wrap every server tool as a CrewAI ``CrewStructuredTool``.

    Returns one ``crewai.tools.CrewStructuredTool`` per registered server
    tool, carrying its name, description, JSON input schema and callable.

    Raises:
        ImportError: if CrewAI is not installed
            (``pip install bankstatementparser-mcp[crewai]``).
    """
    try:
        from crewai.tools import CrewStructuredTool
    except ImportError as exc:
        raise ImportError(
            "CrewAI is not installed. Install it with "
            "`pip install bankstatementparser-mcp[crewai]`."
        ) from exc

    return [
        CrewStructuredTool.from_function(
            func=_tool_func(tool),
            name=_tool_name(tool),
            description=_tool_desc(tool),
            args_schema=_tool_schema(tool),
        )
        for tool in _gateway_tools()
    ]


def as_llamaindex_tools() -> list[Any]:
    """Wrap every server tool as a LlamaIndex ``FunctionTool``.

    Returns one ``llama_index.core.tools.FunctionTool`` per registered server
    tool, carrying its name, description, JSON input schema and callable.

    Raises:
        ImportError: if ``llama-index-core`` is not installed
            (``pip install bankstatementparser-mcp[llamaindex]``).
    """
    try:
        from llama_index.core.tools import FunctionTool
    except ImportError as exc:
        raise ImportError(
            "LlamaIndex is not installed. Install it with "
            "`pip install bankstatementparser-mcp[llamaindex]`."
        ) from exc

    return [
        FunctionTool.from_defaults(
            fn=_tool_func(tool),
            name=_tool_name(tool),
            description=_tool_desc(tool),
            fn_schema=_tool_schema(tool),
        )
        for tool in _gateway_tools()
    ]
