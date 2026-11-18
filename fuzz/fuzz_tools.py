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

"""Coverage-guided Atheris fuzz target for the MCP statement tools.

Each input picks a filename hint and an optional format, then sends
the rest of the bytes as inline statement text to every tool that
takes a payload. The tools promise one failure mode for bad input:
``ToolError``, which the SDK relays to the client. Any other exception
escapes the target and libFuzzer records it as a crash, because the
client would only see a bare "Error executing tool".
``validate_statement`` refuses only an unsupported format; for anything
else it must return its structured verdict.

Run (Linux x86_64, Python 3.12+, ``poetry install --with fuzz``)::

    python fuzz/fuzz_tools.py -max_total_time=60
"""

from __future__ import annotations

import contextlib
import logging
import sys

import atheris

# Core logs a warning or error for nearly every malformed payload;
# at fuzzing speed that output would bury libFuzzer's own report.
logging.disable(logging.CRITICAL)

with atheris.instrument_imports():
    from bankstatementparser_mcp._mcp_compat import ToolError
    from bankstatementparser_mcp.server import (
        detect_format,
        parse_statement,
        summarize_statement,
        validate_statement,
    )

_FILENAMES = (
    None,
    "statement.xml",
    "statement.csv",
    "statement.ofx",
    "statement.qfx",
    "statement.mt940",
    "statement.sta",
    "statement.txt",
)
_SUPPORTED = (None, "camt", "pain001", "csv", "ofx", "qfx", "mt940")
_FORMATS = (*_SUPPORTED, "x")


def _pick(fdp: atheris.FuzzedDataProvider, choices: tuple) -> object:
    """Choose one element of ``choices`` from the fuzz input."""
    return choices[fdp.ConsumeIntInRange(0, len(choices) - 1)]


def test_one_input(data: bytes) -> None:
    """Drive every payload-taking tool with one fuzz input."""
    fdp = atheris.FuzzedDataProvider(data)
    filename = _pick(fdp, _FILENAMES)
    fmt = _pick(fdp, _FORMATS)
    content = fdp.ConsumeUnicodeNoSurrogates(fdp.remaining_bytes())

    # ToolError is the tools' promised refusal of bad input, so it is
    # the one outcome that is not a finding; anything else escapes.
    for tool in (parse_statement, summarize_statement):
        with contextlib.suppress(ToolError):
            tool(content=content, filename=filename, format=fmt)
    with contextlib.suppress(ToolError):
        detect_format(content=content, filename=filename or "statement.xml")

    try:
        verdict = validate_statement(
            content=content, filename=filename, format=fmt
        )
    except ToolError:
        # Only an unsupported explicit format is refused outright.
        if fmt in _SUPPORTED:
            raise
        return
    if not isinstance(verdict, dict) or "is_valid" not in verdict:
        raise AssertionError(f"validate_statement returned {verdict!r}")


def main() -> None:
    """Hand the target to libFuzzer with the command-line options."""
    atheris.Setup(sys.argv, test_one_input)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
