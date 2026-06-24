# Copyright (C) 2023-2026 Bank Statement Parser. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0

"""Regression suite: every documented python example must actually work.

The docs-accuracy tests check that claims in the docs match the
codebase; this module goes further and *executes* the documented
examples themselves:

* Every fenced ``python`` block in README.md and any ``docs/*.md`` must
  be classified in ``BLOCK_SPECS`` below. Adding a new block to the docs
  without classifying it fails the suite — examples cannot silently rot.
* ``run`` blocks are executed verbatim (in-process) against inline
  fixtures supplied via the block's preamble.
* ``imports`` blocks (the ones that need an external transport or a live
  client) have every import statement executed, so a renamed or removed
  public symbol still fails fast.

Non-python blocks (``bash``, ``json``, ``text``) are not executed.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

import pytest

pytest.importorskip("mcp")

REPO_ROOT = Path(__file__).resolve().parents[1]
DOC_FILES = ("README.md",) + tuple(
    str(p.relative_to(REPO_ROOT))
    for p in sorted((REPO_ROOT / "docs").glob("*.md"))
)


# ----------------------------------------------------------------------
# Block extraction
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class DocBlock:
    """One fenced code block extracted from a markdown doc."""

    doc: str
    line: int
    lang: str
    body: str

    @property
    def location(self) -> str:
        """A ``file:line`` label for diagnostics and test ids."""
        return f"{self.doc}:{self.line}"


def _extract_blocks() -> list[DocBlock]:
    """Pull every fenced code block out of the scanned doc files."""
    blocks: list[DocBlock] = []
    for rel in DOC_FILES:
        text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        for match in re.finditer(
            r"^```(\w*)\n(.*?)^```", text, re.DOTALL | re.MULTILINE
        ):
            blocks.append(
                DocBlock(
                    doc=rel,
                    line=text[: match.start()].count("\n") + 1,
                    lang=match.group(1),
                    body=match.group(2),
                )
            )
    return blocks


ALL_BLOCKS = _extract_blocks()
PYTHON_BLOCKS = [b for b in ALL_BLOCKS if b.lang == "python"]


# ----------------------------------------------------------------------
# Classification registry
# ----------------------------------------------------------------------

_CSV_PREAMBLE = ""  # the README block defines its own CSV fixture inline


@dataclass(frozen=True)
class BlockSpec:
    """How to exercise one documented python block.

    ``marker`` is a substring unique to exactly one block across all
    scanned docs. ``mode`` is ``"run"`` (executed verbatim) or
    ``"imports"`` (only the import statements are run).
    """

    marker: str
    mode: str = "run"
    preamble: str = ""
    reason: str = ""


BLOCK_SPECS: tuple[BlockSpec, ...] = (
    # README — "Using the tools": call the tools in-process on inline CSV.
    BlockSpec(
        marker='print(detect_format(csv, "statement.csv"))',
        preamble=_CSV_PREAMBLE,
    ),
    # README — read the resource and prompt functions in-process.
    BlockSpec(
        marker="print(formats_resource())",
        preamble=_CSV_PREAMBLE,
    ),
)


def _matching_blocks(spec: BlockSpec) -> list[DocBlock]:
    """Return every python block whose body contains ``spec.marker``."""
    return [b for b in PYTHON_BLOCKS if spec.marker in b.body]


# ----------------------------------------------------------------------
# Structural guarantees
# ----------------------------------------------------------------------


@pytest.mark.parametrize(
    "block", PYTHON_BLOCKS, ids=[b.location for b in PYTHON_BLOCKS]
)
def test_python_block_is_valid_syntax(block: DocBlock) -> None:
    """Every documented python block parses as valid Python."""
    ast.parse(block.body, filename=block.location)


def test_every_python_block_is_classified() -> None:
    """Each documented python block maps to exactly one BlockSpec."""
    unmatched = [
        b.location
        for b in PYTHON_BLOCKS
        if not any(spec.marker in b.body for spec in BLOCK_SPECS)
    ]
    assert not unmatched, (
        "Unclassified python blocks in docs (add a BlockSpec so the "
        f"example is executed by the regression suite): {unmatched}"
    )

    for spec in BLOCK_SPECS:
        matches = _matching_blocks(spec)
        assert len(matches) == 1, (
            f"BlockSpec marker {spec.marker!r} must match exactly one "
            f"block, matched {[b.location for b in matches]}"
        )


# ----------------------------------------------------------------------
# Execution
# ----------------------------------------------------------------------


def _spec_id(spec: BlockSpec) -> str:
    """A stable id for a BlockSpec parametrisation."""
    blocks = _matching_blocks(spec)
    return blocks[0].location if blocks else spec.marker[:30]


@pytest.mark.parametrize(
    "spec", BLOCK_SPECS, ids=[_spec_id(s) for s in BLOCK_SPECS]
)
def test_documented_python_block(
    spec: BlockSpec,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Every classified python block runs (or imports) cleanly."""
    blocks = _matching_blocks(spec)
    assert len(blocks) == 1
    block = blocks[0]

    if spec.mode == "imports":
        tree = ast.parse(block.body)
        import_lines = [
            ast.unparse(node)
            for node in tree.body
            if isinstance(node, ast.Import | ast.ImportFrom)
        ]
        assert import_lines, (
            f"{block.location} is imports-only ({spec.reason}) but has "
            "no imports to verify"
        )
        namespace: dict[str, object] = {}
        exec(
            compile("\n".join(import_lines), block.location, "exec"),
            namespace,
        )
        return

    namespace = {"__name__": "bsp_mcp_doc_example"}
    if spec.preamble:
        exec(
            compile(spec.preamble, f"{block.location}-preamble", "exec"),
            namespace,
        )
    exec(compile(block.body, block.location, "exec"), namespace)
    capsys.readouterr()  # examples are allowed to print
