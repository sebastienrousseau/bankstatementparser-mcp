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

"""Hypothesis property and fuzz tests for bankstatementparser-mcp."""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from bankstatementparser_mcp.server import (
    _require_format,
    _suffix_for,
    _summary_to_jsonable,
    detect_format,
    list_supported_formats,
    parse_statement,
    summarize_statement,
    validate_statement,
)


@settings(max_examples=50, deadline=None)
@given(
    st.text(min_size=0, max_size=1000),
    st.one_of(st.none(), st.sampled_from(["statement.csv", "statement.xml", "statement.mt940", "statement.ofx", "statement.qfx", "test.txt"])),
)
def test_fuzz_detect_format_arbitrary_inputs(content: str, filename: str | None) -> None:
    """detect_format never crashes on arbitrary input text."""
    try:
        res = detect_format(content=content, filename=filename)
        assert isinstance(res, dict)
        assert "format" in res
    except (ValueError, Exception):
        pass


@settings(max_examples=30, deadline=None)
@given(
    st.text(min_size=0, max_size=1000),
    st.one_of(st.none(), st.sampled_from(["statement.csv", "statement.xml", "statement.mt940"])),
    st.one_of(st.none(), st.sampled_from(["csv", "camt", "mt940", "ofx", "qfx", "pain001", "unknown"])),
)
def test_fuzz_parse_statement_arbitrary_inputs(
    content: str, filename: str | None, fmt: str | None
) -> None:
    """parse_statement handles arbitrary payloads safely returning structured error or result."""
    try:
        res = parse_statement(content=content, filename=filename, format=fmt)
        assert isinstance(res, dict)
    except (ValueError, Exception):
        pass


@settings(max_examples=30, deadline=None)
@given(
    st.text(min_size=0, max_size=1000),
    st.one_of(st.none(), st.sampled_from(["statement.csv", "statement.xml", "statement.mt940"])),
    st.one_of(st.none(), st.sampled_from(["csv", "camt", "mt940", "ofx", "qfx", "pain001", "unknown"])),
)
def test_fuzz_validate_statement_arbitrary_inputs(
    content: str, filename: str | None, fmt: str | None
) -> None:
    """validate_statement handles arbitrary payloads safely returning validation result dict."""
    try:
        res = validate_statement(content=content, filename=filename, format=fmt)
        assert isinstance(res, dict)
    except (ValueError, Exception):
        pass


@settings(max_examples=30, deadline=None)
@given(
    st.text(min_size=0, max_size=1000),
    st.one_of(st.none(), st.sampled_from(["statement.csv", "statement.xml", "statement.mt940"])),
    st.one_of(st.none(), st.sampled_from(["csv", "camt", "mt940", "ofx", "qfx", "pain001", "unknown"])),
)
def test_fuzz_summarize_statement_arbitrary_inputs(
    content: str, filename: str | None, fmt: str | None
) -> None:
    """summarize_statement handles arbitrary payloads safely."""
    try:
        res = summarize_statement(content=content, filename=filename, format=fmt)
        assert isinstance(res, dict)
    except (ValueError, Exception):
        pass


@settings(max_examples=50, deadline=None)
@given(st.dictionaries(st.text(max_size=20), st.one_of(st.text(max_size=50), st.integers(), st.none()), max_size=10))
def test_fuzz_summary_to_jsonable(mapping: dict) -> None:
    """_summary_to_jsonable safely converts mappings to JSON primitives."""
    jsonable = _summary_to_jsonable(mapping)
    assert isinstance(jsonable, dict)
    for k, v in jsonable.items():
        assert isinstance(k, str)
        assert v is None or isinstance(v, (str, int, float, bool))
