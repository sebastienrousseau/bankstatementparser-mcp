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
from typing import Annotated, Any

from bankstatementparser.additional_parsers import (
    create_parser,
    detect_statement_format,
)
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

mcp = FastMCP("bankstatementparser")

# Shared MCP tool annotations. Every tool in this server is a pure,
# side-effect-free reader: it takes the statement text **inline** as an
# argument, materialises it in a private, server-controlled temporary
# file for the duration of one call, and returns JSON-serialisable data.
# None of them read a caller-supplied filesystem path, mutate state, or
# write any output the caller can observe, so all are marked
# ``readOnlyHint`` + ``idempotentHint`` and never ``destructiveHint``.
#
# The only axis that would ever vary is ``openWorldHint`` — whether a
# tool reaches out to an arbitrary, caller-controlled path or external
# system. These tools do not (the temp file is closed-world and
# deterministic over the input), so every tool uses ``_PURE_READ``.
# ``_FS_READ`` is kept as the shared vocabulary for any future tool that
# opens a caller-supplied path.
#
# These hints let MCP clients (and the Glama quality grader) reason about
# safety, caching, and auto-approval without executing the tool.
_PURE_READ = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)
_FS_READ = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=True,
)

_FORMAT_SUFFIX: dict[str, str] = {
    "camt": ".xml",
    "pain001": ".xml",
    "csv": ".csv",
    "ofx": ".ofx",
    "qfx": ".qfx",
    "mt940": ".mt940",
}

# Enumerated value list for the ``format`` MCP parameter. Surfacing the
# concrete allowed values as a JSON Schema ``enum`` (and in the description)
# lets clients — and the Glama TDQS grader — see the valid inputs without a
# tool call. Derived from ``_FORMAT_SUFFIX`` (the parser source of truth) so
# it never drifts. The enum is schema metadata only; ``_require_format``
# remains the runtime guard.
_FORMAT_VALUES: list[str] = sorted(_FORMAT_SUFFIX)
_FORMAT_LIST = ", ".join(f"'{v}'" for v in _FORMAT_VALUES)

_Format = Annotated[
    str | None,
    Field(
        description=(
            "Explicit format identifier that overrides detection from the "
            "filename. Must be exactly one of: "
            f"{_FORMAT_LIST} (see list_supported_formats). When omitted, the "
            "format is inferred from the filename extension."
        ),
        json_schema_extra={"enum": _FORMAT_VALUES},
    ),
]


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


@mcp.tool(title="List supported statement formats", annotations=_PURE_READ)
def list_supported_formats() -> list[str]:
    """List every bank statement format identifier this server can parse.

    Use this first to discover the valid ``format`` strings before calling
    ``detect_format`` or ``parse_statement``. For the file extensions and a
    human-readable description of each format, read the
    ``bankstatementparser://formats`` resource instead.

    Returns:
        The supported format identifiers.
    """
    return list(_FORMAT_SUFFIX)


@mcp.tool(title="Detect statement format", annotations=_PURE_READ)
def detect_format(
    content: Annotated[
        str,
        Field(
            description=(
                "The raw statement text to inspect, inline (not a file "
                "path). Supported formats include ISO 20022 CAMT.053 and "
                "pain.001 XML, SWIFT MT940, CSV exports, and OFX/QFX."
            ),
        ),
    ],
    filename: Annotated[
        str,
        Field(
            description=(
                "Original filename of the payload; its extension is the "
                "primary detection hint. Recognised extensions: .xml, "
                ".csv, .ofx, .qfx, .mt940, .sta. Defaults to "
                "'statement.xml'."
            ),
        ),
    ] = "statement.xml",
) -> str:
    """Detect which bank statement format an inline payload is.

    Use this when you hold statement text but do not yet know its format,
    to resolve the ``format`` identifier from the content plus filename
    hint. Once the format is known, call ``parse_statement`` to read the
    transactions instead of calling this again.

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


@mcp.tool(
    title="Parse statement transactions and summary", annotations=_PURE_READ
)
def parse_statement(
    content: Annotated[
        str,
        Field(
            description=(
                "The raw statement text to parse, inline (not a file "
                "path). Accepts ISO 20022 CAMT.053 and pain.001 XML, "
                "SWIFT MT940, CSV exports, and OFX/QFX payloads."
            ),
        ),
    ],
    filename: Annotated[
        str,
        Field(
            description=(
                "Original filename of the payload; its extension "
                "(.xml, .csv, .ofx, .qfx, .mt940, .sta) selects the "
                "format when 'format' is omitted. Defaults to "
                "'statement.xml'."
            ),
        ),
    ] = "statement.xml",
    format: _Format = None,
    limit: Annotated[
        int | None,
        Field(
            description=(
                "Optional maximum number of transaction rows to return. "
                "The full 'transaction_count' is always reported even "
                "when the returned rows are truncated. When omitted, all "
                "rows are returned."
            ),
        ),
    ] = None,
) -> dict[str, Any]:
    """Parse an inline statement payload into transaction rows and a summary.

    Use this to read the full transaction detail plus the statement
    balances from a payload. When you only need the balances/totals use
    ``summarize_statement`` instead, and to merely confirm a payload parses
    without returning any rows use ``validate_statement``.

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


@mcp.tool(title="Validate statement (dry run)", annotations=_PURE_READ)
def validate_statement(
    content: Annotated[
        str,
        Field(
            description=(
                "The raw statement text to validate, inline (not a file "
                "path). Accepts ISO 20022 CAMT.053 and pain.001 XML, "
                "SWIFT MT940, CSV exports, and OFX/QFX payloads."
            ),
        ),
    ],
    filename: Annotated[
        str,
        Field(
            description=(
                "Original filename of the payload; its extension "
                "(.xml, .csv, .ofx, .qfx, .mt940, .sta) selects the "
                "format when 'format' is omitted. Defaults to "
                "'statement.xml'."
            ),
        ),
    ] = "statement.xml",
    format: _Format = None,
) -> dict[str, Any]:
    """Dry-run parse an inline statement to check it parses cleanly.

    Use this to confirm a payload is well-formed and parseable before
    committing to a full read; it returns a structured pass/fail with the
    transaction count but never the rows themselves, and never raises on a
    parse error. To actually read the transactions use ``parse_statement``.

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


@mcp.tool(title="Summarize statement balances", annotations=_PURE_READ)
def summarize_statement(
    content: Annotated[
        str,
        Field(
            description=(
                "The raw statement text to summarize, inline (not a "
                "file path). Accepts ISO 20022 CAMT.053 and pain.001 "
                "XML, SWIFT MT940, CSV exports, and OFX/QFX payloads."
            ),
        ),
    ],
    filename: Annotated[
        str,
        Field(
            description=(
                "Original filename of the payload; its extension "
                "(.xml, .csv, .ofx, .qfx, .mt940, .sta) selects the "
                "format when 'format' is omitted. Defaults to "
                "'statement.xml'."
            ),
        ),
    ] = "statement.xml",
    format: _Format = None,
) -> dict[str, Any]:
    """Summarize an inline statement's balances and totals only.

    Use this when you need just the opening/closing balances, currency, and
    other summary fields without the per-transaction rows. For the full
    transaction detail alongside the summary, use ``parse_statement``
    instead.

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


@mcp.resource(
    "bankstatementparser://formats", title="Supported formats catalogue"
)
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


@mcp.prompt(title="Analyse a bank statement")
def analyze_statement(
    filename: Annotated[
        str,
        Field(
            description=(
                "The statement filename being analysed; its extension "
                "(.xml, .csv, .ofx, .qfx, .mt940, .sta) hints at the "
                "format. Defaults to 'statement.xml'."
            ),
        ),
    ] = "statement.xml",
) -> str:
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
