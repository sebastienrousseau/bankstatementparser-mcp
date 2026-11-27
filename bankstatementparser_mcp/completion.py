# SPDX-License-Identifier: Apache-2.0 OR MIT
"""The ``bankstatementparser-mcp`` parser, for shell-completion generation.

``make completions`` runs ``shtab bankstatementparser_mcp.completion.parser``
and writes ``completions/``; CI regenerates them and fails on any
difference. The parser is the one ``server.main`` parses with
(:func:`bankstatementparser_mcp._cli.build_parser`), so the completions
cannot drift from the flags the server takes. Importing this module does
not import the MCP server.
"""

from __future__ import annotations

import argparse

from bankstatementparser_mcp import __version__, _cli

PROG = "bankstatementparser-mcp"


def parser() -> argparse.ArgumentParser:
    """Return the console script's argument parser."""
    return _cli.build_parser(PROG, __version__)
