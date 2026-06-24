# Copyright (C) 2023-2026 Bank Statement Parser. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

"""In-process tests for the bankstatementparser-mcp server.

Every tool, helper, the resource, and the prompt are exercised to 100%
line and branch coverage. The fixtures are inline statement payloads so
the suite is self-contained and offline.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

pytest.importorskip("mcp")

from bankstatementparser.exceptions import ValidationError  # noqa: E402

import bankstatementparser_mcp.server as server  # noqa: E402

CSV = (
    "date,description,amount,currency,balance\n"
    "2023-01-02,Salary,500.00,EUR,1500.00\n"
    "2023-01-03,Groceries,-40.50,EUR,1459.50\n"
)

MT940 = (
    ":20:STARTUMS\n"
    ":25:1234567890\n"
    ":28C:00001/001\n"
    ":60F:C230101EUR1000,00\n"
    ":61:2301020102C500,00NTRFNONREF//abc\n"
    ":86:Salary payment\n"
    ":62F:C230102EUR1500,00"
)


# --------------------------------------------------------------------------
# list_supported_formats
# --------------------------------------------------------------------------
def test_list_supported_formats() -> None:
    """The full supported-format set is returned."""
    formats = server.list_supported_formats()
    assert formats == ["camt", "pain001", "csv", "ofx", "qfx", "mt940"]


# --------------------------------------------------------------------------
# _require_format
# --------------------------------------------------------------------------
def test_require_format_accepts_known() -> None:
    """A supported format passes silently."""
    assert server._require_format("csv") is None


def test_require_format_rejects_unknown() -> None:
    """An unsupported format raises ValueError listing the valid set."""
    with pytest.raises(ValueError, match="Unsupported format 'nope'"):
        server._require_format("nope")


# --------------------------------------------------------------------------
# _suffix_for
# --------------------------------------------------------------------------
def test_suffix_for_uses_filename_extension() -> None:
    """A recognised filename extension is reused verbatim."""
    assert server._suffix_for("statement.csv", None) == ".csv"


def test_suffix_for_accepts_sta_extension() -> None:
    """The MT940 ``.sta`` extension is accepted."""
    assert server._suffix_for("statement.sta", None) == ".sta"


def test_suffix_for_falls_back_to_format() -> None:
    """An unusable extension falls back to the explicit format suffix."""
    assert server._suffix_for("statement.txt", "mt940") == ".mt940"


def test_suffix_for_no_filename_uses_format() -> None:
    """An empty filename falls straight through to the format suffix."""
    assert server._suffix_for("", "csv") == ".csv"


def test_suffix_for_raises_without_hint() -> None:
    """No usable extension and no format raises a guiding ValueError."""
    with pytest.raises(ValueError, match="Provide a 'filename'"):
        server._suffix_for("statement.txt", None)


# --------------------------------------------------------------------------
# detect_format
# --------------------------------------------------------------------------
def test_detect_format_csv() -> None:
    """A CSV payload is detected as ``csv``."""
    assert server.detect_format(CSV, "statement.csv") == "csv"


def test_detect_format_mt940() -> None:
    """An MT940 payload is detected as ``mt940``."""
    assert server.detect_format(MT940, "statement.mt940") == "mt940"


def test_detect_format_failure() -> None:
    """An undetectable payload raises ValidationError."""
    with pytest.raises(ValidationError):
        server.detect_format("<unknown/>", "mystery.xml")


def test_detect_format_garbage_with_csv_hint() -> None:
    """Garbage content with a ``.csv`` hint detects via the extension."""
    assert server.detect_format("garbage nonsense", "statement.csv") == "csv"


# --------------------------------------------------------------------------
# parse_statement
# --------------------------------------------------------------------------
def test_parse_statement_csv_full() -> None:
    """A CSV payload parses into both transactions and a summary."""
    result = server.parse_statement(CSV, "statement.csv")
    assert result["format"] == "csv"
    assert result["transaction_count"] == 2
    assert len(result["transactions"]) == 2
    assert "amount" in result["columns"]
    assert isinstance(result["summary"], dict)


def test_parse_statement_mt940_explicit_format() -> None:
    """An explicit format override is honoured."""
    result = server.parse_statement(MT940, "statement.mt940", format="mt940")
    assert result["format"] == "mt940"
    assert result["transaction_count"] == 1


def test_parse_statement_limit_truncates() -> None:
    """A limit truncates the returned rows but not the count."""
    result = server.parse_statement(CSV, "statement.csv", limit=1)
    assert result["transaction_count"] == 2
    assert len(result["transactions"]) == 1


def test_parse_statement_rejects_unknown_format() -> None:
    """An unsupported explicit format is rejected before parsing."""
    with pytest.raises(ValueError, match="Unsupported format 'nope'"):
        server.parse_statement(CSV, "statement.csv", format="nope")


def test_parse_statement_limit_zero_returns_no_rows() -> None:
    """A ``limit`` of 0 returns no rows but keeps the full count."""
    result = server.parse_statement(CSV, "statement.csv", limit=0)
    assert result["transaction_count"] == 2
    assert result["transactions"] == []


def test_parse_statement_limit_above_row_count() -> None:
    """A ``limit`` larger than the row count returns every row."""
    result = server.parse_statement(CSV, "statement.csv", limit=99)
    assert result["transaction_count"] == 2
    assert len(result["transactions"]) == 2


def test_parse_statement_malformed_xml_raises() -> None:
    """A malformed XML payload surfaces the parser's ValidationError."""
    with pytest.raises(ValidationError):
        server.parse_statement("<not valid xml", "statement.xml")


def test_parse_statement_explicit_wrong_format() -> None:
    """CSV content parsed as MT940 yields a structurally empty result."""
    result = server.parse_statement(CSV, "statement.csv", format="mt940")
    assert result["format"] == "mt940"
    assert result["transaction_count"] == 0
    assert result["transactions"] == []


# --------------------------------------------------------------------------
# validate_statement
# --------------------------------------------------------------------------
def test_validate_statement_ok() -> None:
    """A valid CSV payload validates cleanly."""
    result = server.validate_statement(CSV, "statement.csv")
    assert result["is_valid"] is True
    assert result["format"] == "csv"
    assert result["transaction_count"] == 2
    assert result["error"] is None


def test_validate_statement_error() -> None:
    """An undetectable payload returns a structured failure."""
    result = server.validate_statement("<unknown/>", "mystery.xml")
    assert result["is_valid"] is False
    assert result["transaction_count"] == 0
    assert result["error"]


def test_validate_statement_rejects_unknown_format() -> None:
    """An unsupported explicit format is rejected up front."""
    with pytest.raises(ValueError, match="Unsupported format 'nope'"):
        server.validate_statement(CSV, "statement.csv", format="nope")


def test_validate_statement_malformed_xml_structured_error() -> None:
    """Malformed XML is reported as a structured error, never raised."""
    result = server.validate_statement("<not valid xml", "statement.xml")
    assert result["is_valid"] is False
    assert result["format"] is None
    assert result["transaction_count"] == 0
    assert isinstance(result["error"], str) and result["error"]


def test_validate_statement_explicit_wrong_format() -> None:
    """An explicit-but-wrong format keeps the resolved format on output."""
    result = server.validate_statement(CSV, "statement.csv", format="mt940")
    assert result["is_valid"] is True
    assert result["format"] == "mt940"
    assert result["transaction_count"] == 0


# --------------------------------------------------------------------------
# summarize_statement (garbage path)
# --------------------------------------------------------------------------
def test_summarize_statement_garbage_raises() -> None:
    """An undetectable payload raises rather than returning a summary."""
    with pytest.raises(ValidationError):
        server.summarize_statement("<unknown/>", "mystery.xml")


# --------------------------------------------------------------------------
# summarize_statement
# --------------------------------------------------------------------------
def test_summarize_statement_mt940() -> None:
    """The MT940 summary surfaces the balances and currency."""
    summary = server.summarize_statement(MT940, "statement.mt940")
    assert summary["currency"] == "EUR"
    assert summary["opening_balance"] == "1000.00"
    assert summary["closing_balance"] == "1500.00"


def test_summarize_statement_rejects_unknown_format() -> None:
    """An unsupported explicit format is rejected before parsing."""
    with pytest.raises(ValueError, match="Unsupported format 'nope'"):
        server.summarize_statement(CSV, "statement.csv", format="nope")


# --------------------------------------------------------------------------
# resource + prompt
# --------------------------------------------------------------------------
def test_formats_resource() -> None:
    """The resource lists every supported format."""
    text = server.formats_resource()
    for name in server.list_supported_formats():
        assert name in text


def test_analyze_statement_prompt() -> None:
    """The prompt mentions the filename and the tool chain."""
    prompt = server.analyze_statement("statement.csv")
    assert "statement.csv" in prompt
    assert "detect_format" in prompt
    assert "summarize_statement" in prompt


# --------------------------------------------------------------------------
# example scripts
# --------------------------------------------------------------------------
@pytest.mark.parametrize(
    "module_path",
    [
        "examples/01_mcp_tools.py",
        "examples/02_validate_pipeline.py",
        "examples/03_parse_bank_replies.py",
        "examples/04_resource_and_prompt.py",
    ],
)
def test_example_scripts_run_without_error(module_path: str) -> None:
    """Each example script imports and runs end-to-end."""
    path = Path(__file__).resolve().parents[1] / module_path
    spec = importlib.util.spec_from_file_location(
        f"_example_{path.stem}", path
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.main()
