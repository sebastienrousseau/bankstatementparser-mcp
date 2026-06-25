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

"""BankStatementParser MCP server (stdio transport).

Tools, the resource, and the prompt are thin adapters over the
bankstatementparser parser core. The tools take **inline content**
(the raw text of a statement) plus a filename hint, because an MCP
client does not share the server's filesystem. Each call materialises
the content in a private temporary file, runs the same
``create_parser`` pipeline the CLI uses, and returns plain
JSON-serialisable data.

Run it with::

    bankstatementparser-mcp
"""

from __future__ import annotations

import os
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from bankstatementparser.additional_parsers import (
    create_parser,
    detect_statement_format,
)
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("bankstatementparser")

_FORMAT_SUFFIX: dict[str, str] = {
    "camt": ".xml",
    "pain001": ".xml",
    "csv": ".csv",
    "ofx": ".ofx",
    "qfx": ".qfx",
    "mt940": ".mt940",
}


def _require_format(format_name: str) -> None:
    """Reject an unsupported statement format.

    Args:
        format_name: The statement format to check.

    Raises:
        ValueError: If the format is not supported.
    """
    if format_name not in _FORMAT_SUFFIX:
        supported = ", ".join(_FORMAT_SUFFIX)
        raise ValueError(
            f"Unsupported format '{format_name}'. Supported: {supported}"
        )


def _suffix_for(filename: str | None, format_name: str | None) -> str:
    """Choose the temp-file suffix for an inline payload.

    Args:
        filename: Optional original filename whose extension is reused
            when it is one the parser accepts.
        format_name: Optional explicit format, used when no usable
            filename extension is available.

    Returns:
        A file suffix (including the leading dot) for the temp file.

    Raises:
        ValueError: If neither a usable extension nor a supported
            format is provided.
    """
    if filename:
        suffix = Path(filename).suffix.lower()
        if suffix in set(_FORMAT_SUFFIX.values()) | {".sta"}:
            return suffix
    if format_name:
        _require_format(format_name)
        return _FORMAT_SUFFIX[format_name]
    raise ValueError(
        "Provide a 'filename' with a supported extension "
        "(.xml/.csv/.ofx/.qfx/.mt940/.sta) or an explicit 'format'."
    )


@contextmanager
def _materialise(content: str, suffix: str) -> Iterator[Path]:
    """Write inline content to a private temp file for one call.

    A closed-then-reopened temp file (via :func:`tempfile.mkstemp`) is
    used rather than an open ``NamedTemporaryFile`` so the file-based
    parsers can reopen the path by name.

    Args:
        content: The raw statement text supplied by the client.
        suffix: The file suffix to give the temp file.

    Yields:
        The path to the temporary file (removed on exit).
    """
    fd, name = tempfile.mkstemp(suffix=suffix)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
        yield Path(name)
    finally:
        os.unlink(name)


def _summary_to_jsonable(summary: dict[str, Any]) -> dict[str, Any]:
    """Coerce a summary record to JSON-serialisable primitives.

    Args:
        summary: The raw summary record from a parser.

    Returns:
        The same mapping with non-primitive values stringified.
    """
    jsonable: dict[str, Any] = {}
    for key, value in summary.items():
        if value is None or isinstance(value, str | int | bool):
            jsonable[key] = value
        else:
            jsonable[key] = str(value)
    return jsonable


@mcp.tool()
def list_supported_formats() -> list[str]:
    """List every bank statement format the parser can read.

    Returns:
        The supported format identifiers.
    """
    return list(_FORMAT_SUFFIX)


@mcp.tool()
def detect_format(content: str, filename: str = "statement.xml") -> str:
    """Detect which statement format a payload is.

    Args:
        content: The raw statement text.
        filename: Original filename; its extension is the primary hint.

    Returns:
        The detected format identifier.

    Raises:
        ValueError: If the format cannot be detected.
    """
    suffix = _suffix_for(filename, None)
    with _materialise(content, suffix) as path:
        return detect_statement_format(path)


@mcp.tool()
def parse_statement(
    content: str,
    filename: str = "statement.xml",
    format: str | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    """Parse a statement into structured transactions and a summary.

    Args:
        content: The raw statement text.
        filename: Original filename; its extension selects the format
            when ``format`` is omitted.
        format: Explicit format override.
        limit: Optional cap on returned transaction rows.

    Returns:
        A dict with the resolved ``format``, ``columns``, full
        ``transaction_count``, the (possibly truncated) ``transactions``
        as row dicts, and the statement ``summary``.

    Raises:
        ValueError: If the format is unsupported or cannot be detected.
    """
    if format is not None:
        _require_format(format)
    suffix = _suffix_for(filename, format)
    with _materialise(content, suffix) as path:
        parser = create_parser(path, format)
        frame = parser.parse()
        summary = _summary_to_jsonable(dict(parser.get_summary()))
        records = frame.to_dict("records")
        total = len(records)
        if limit is not None:
            records = records[:limit]
        return {
            "format": format or detect_statement_format(path),
            "columns": list(frame.columns),
            "transaction_count": total,
            "transactions": [
                {k: (v if v is None else str(v)) for k, v in row.items()}
                for row in records
            ],
            "summary": summary,
        }


@mcp.tool()
def validate_statement(
    content: str,
    filename: str = "statement.xml",
    format: str | None = None,
) -> dict[str, Any]:
    """Check whether a statement parses cleanly (a dry run).

    Args:
        content: The raw statement text.
        filename: Original filename; its extension selects the format.
        format: Explicit format override.

    Returns:
        A dict with ``is_valid``, the resolved ``format``, the
        ``transaction_count`` on success, and an ``error`` on failure.
    """
    if format is not None:
        _require_format(format)
    try:
        suffix = _suffix_for(filename, format)
        with _materialise(content, suffix) as path:
            resolved = format or detect_statement_format(path)
            parser = create_parser(path, format)
            frame = parser.parse()
        return {
            "is_valid": True,
            "format": resolved,
            "transaction_count": len(frame),
            "error": None,
        }
    except Exception as exc:
        return {
            "is_valid": False,
            "format": format,
            "transaction_count": 0,
            "error": str(exc),
        }


@mcp.tool()
def summarize_statement(
    content: str,
    filename: str = "statement.xml",
    format: str | None = None,
) -> dict[str, Any]:
    """Return only the statement summary (no per-transaction rows).

    Args:
        content: The raw statement text.
        filename: Original filename; its extension selects the format.
        format: Explicit format override.

    Returns:
        The summary record with Decimal values stringified.

    Raises:
        ValueError: If the format is unsupported or cannot be detected.
    """
    if format is not None:
        _require_format(format)
    suffix = _suffix_for(filename, format)
    with _materialise(content, suffix) as path:
        parser = create_parser(path, format)
        return _summary_to_jsonable(dict(parser.get_summary()))


@mcp.resource("bankstatementparser://formats")
def formats_resource() -> str:
    """Describe each supported statement format and its file extensions.

    Returns:
        A human-readable catalogue of the supported formats.
    """
    lines = [
        "BankStatementParser supported input formats:",
        "",
        "- camt    : ISO 20022 CAMT.053 statements (.xml)",
        "- pain001 : ISO 20022 pain.001 credit-transfer (.xml)",
        "- csv     : delimited statement exports (.csv)",
        "- ofx     : Open Financial Exchange (.ofx)",
        "- qfx     : Quicken Financial Exchange (.qfx)",
        "- mt940   : SWIFT MT940 statement messages (.mt940, .sta)",
    ]
    return "\n".join(lines)


@mcp.prompt()
def analyze_statement(filename: str = "statement.xml") -> str:
    """Guided prompt for reading and reconciling a bank statement.

    Args:
        filename: The statement filename being analysed.

    Returns:
        A prompt string instructing the model how to proceed.
    """
    return (
        f"Help me analyse the bank statement '{filename}'. First call "
        "detect_format with its content to confirm the format, then "
        "validate_statement to make sure it parses, then parse_statement "
        "to read the transactions and summarize_statement for the "
        "opening/closing balances. Reconcile the transaction total "
        "against the balances and flag anything that looks off."
    )


def main() -> None:
    """Run the BankStatementParser MCP server over stdio."""
    mcp.run()


if __name__ == "__main__":  # pragma: no cover
    main()
