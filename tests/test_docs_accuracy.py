# Copyright (C) 2023-2026 Bank Statement Parser. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0

"""Automated validation that README, docs, and examples stay in sync
with the actual codebase.

If any of these tests fail, the corresponding markdown file has a
stale claim that a human will trust and act on. Fix the docs, not
the test.
"""

from __future__ import annotations

import asyncio
import re
from pathlib import Path

import pytest

pytest.importorskip("mcp")

import bankstatementparser_mcp  # noqa: E402
import bankstatementparser_mcp.server as server  # noqa: E402

# ---------------------------------------------------------------------------
# Repo paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[1]
README = REPO_ROOT / "README.md"
CHANGELOG = REPO_ROOT / "CHANGELOG.md"
PYPROJECT = REPO_ROOT / "pyproject.toml"
EXAMPLES_DIR = REPO_ROOT / "examples"
EXAMPLES_README = EXAMPLES_DIR / "README.md"


def _read(path: Path) -> str:
    """Read a UTF-8 text file."""
    return path.read_text(encoding="utf-8")


# Word forms used for small-integer claims like "the five tools".
_NUMBER_WORDS = {
    1: "one",
    2: "two",
    3: "three",
    4: "four",
    5: "five",
    6: "six",
    7: "seven",
}


def _pyproject_version() -> str:
    """The ``[tool.poetry] version`` string from pyproject.toml."""
    match = re.search(
        r'^version\s*=\s*"([^"]+)"', _read(PYPROJECT), re.MULTILINE
    )
    assert match is not None, "pyproject.toml has no version field"
    return match.group(1)


def _tool_names() -> list[str]:
    """Every ``@mcp.tool()`` name registered on the server."""
    return [tool.name for tool in asyncio.run(server.mcp.list_tools())]


def _prompt_names() -> list[str]:
    """Every ``@mcp.prompt()`` name registered on the server."""
    return [p.name for p in asyncio.run(server.mcp.list_prompts())]


def _resource_uris() -> list[str]:
    """Every ``@mcp.resource()`` URI registered on the server."""
    return [str(r.uri) for r in asyncio.run(server.mcp.list_resources())]


def _public_symbols() -> list[str]:
    """Every public tool, the resource fn, and the prompt fn name.

    The tool and prompt names come straight from the live MCP registry;
    the resource and prompt python function names are added so the
    in-process call sites stay documented too.
    """
    return [
        *_tool_names(),
        *_prompt_names(),
        "formats_resource",
    ]


# ---------------------------------------------------------------------------
# 1. Version consistency
# ---------------------------------------------------------------------------


class TestVersionConsistency:
    """The package version agrees across metadata, code, and docs."""

    def test_package_version_matches_pyproject(self) -> None:
        assert bankstatementparser_mcp.__version__ == _pyproject_version()

    def test_changelog_has_current_version_entry(self) -> None:
        version = _pyproject_version()
        assert f"[{version}]" in _read(
            CHANGELOG
        ), f"CHANGELOG has no entry for current version {version}"

    def test_version_pinned_at_expected_release(self) -> None:
        # The companion package stays at 0.0.13 until a real release.
        assert bankstatementparser_mcp.__version__ == "0.0.13"


# ---------------------------------------------------------------------------
# 2. README documents the full public surface
# ---------------------------------------------------------------------------


class TestReadmeApiSurface:
    """Every public tool, resource, and prompt appears in README.md."""

    readme_text = _read(README)

    def test_all_public_symbols_mentioned(self) -> None:
        for sym in _public_symbols():
            assert (
                sym in self.readme_text
            ), f"README doesn't mention public symbol '{sym}'"

    def test_resource_uri_mentioned(self) -> None:
        for uri in _resource_uris():
            assert (
                uri in self.readme_text
            ), f"README doesn't mention resource URI '{uri}'"

    def test_supported_formats_all_mentioned(self) -> None:
        for fmt in server.list_supported_formats():
            assert (
                fmt in self.readme_text
            ), f"README doesn't mention supported format '{fmt}'"


# ---------------------------------------------------------------------------
# 3. Numeric / counting claims match reality
# ---------------------------------------------------------------------------


class TestReadmeCounts:
    """Counting claims ('five tools', 'one resource') are accurate."""

    readme_text = _read(README)

    def test_tool_count_word_matches(self) -> None:
        actual = len(_tool_names())
        word = _NUMBER_WORDS[actual]
        assert (
            f"{word} tools" in self.readme_text
        ), f"README should say '{word} tools' (there are {actual})"

    def test_one_resource_one_prompt_claim(self) -> None:
        assert "one resource and one prompt" in self.readme_text

    def test_no_stale_digit_tool_count(self) -> None:
        # Guard against a stray "N tools" digit claim disagreeing with
        # the word claim verified above.
        actual = len(_tool_names())
        for claimed in re.findall(r"(\d+)\s+tools", self.readme_text):
            assert (
                int(claimed) == actual
            ), f"README claims {claimed} tools but there are {actual}"


# ---------------------------------------------------------------------------
# 4. Example files referenced in docs exist
# ---------------------------------------------------------------------------


class TestExamplesExist:
    """Every example path referenced in the docs exists on disk."""

    readme_text = _read(README)
    examples_readme_text = _read(EXAMPLES_README)

    def _referenced_scripts(self, text: str) -> list[str]:
        """Pull ``examples/<name>.py`` / ``<name>.py`` references."""
        return re.findall(r"`?(?:examples/)?([\w]+\.py)`?", text)

    def test_readme_example_dir_referenced(self) -> None:
        assert "examples/" in self.readme_text

    def test_examples_readme_scripts_exist(self) -> None:
        for script in self._referenced_scripts(self.examples_readme_text):
            assert (
                EXAMPLES_DIR / script
            ).exists(), (
                f"examples/README.md references {script} but it is missing"
            )

    def test_every_example_is_listed_in_examples_readme(self) -> None:
        listed = set(self._referenced_scripts(self.examples_readme_text))
        for py in EXAMPLES_DIR.glob("*.py"):
            assert py.name in listed, (
                f"examples/{py.name} exists but is not listed in "
                "examples/README.md"
            )


# ---------------------------------------------------------------------------
# 5. Examples cover the whole public surface
# ---------------------------------------------------------------------------


class TestExamplesCoverSurface:
    """Each public symbol is exercised by at least one example."""

    def _examples_source(self) -> str:
        return "\n".join(_read(py) for py in sorted(EXAMPLES_DIR.glob("*.py")))

    def test_every_public_symbol_demonstrated(self) -> None:
        source = self._examples_source()
        for sym in _public_symbols():
            assert (
                sym in source
            ), f"No example exercises the public symbol '{sym}'"


# ---------------------------------------------------------------------------
# 6. Development section claims match the gates
# ---------------------------------------------------------------------------


class TestDevelopmentClaims:
    """The README's stated quality posture matches pyproject's gates."""

    readme_text = _read(README)

    def test_coverage_floor_claim(self) -> None:
        pyproject = _read(PYPROJECT)
        if "fail_under = 100" in pyproject:
            assert "100% line + branch coverage" in self.readme_text

    def test_python_minimum_matches_pyproject(self) -> None:
        pyproject = _read(PYPROJECT)
        if ">=3.10" in pyproject:
            assert (
                "3.10" in self.readme_text
            ), "README should mention the Python 3.10 minimum"

    def test_core_dependency_floor_matches(self) -> None:
        pyproject = _read(PYPROJECT)
        match = re.search(
            r'bankstatementparser\s*=\s*">=([0-9.]+)"', pyproject
        )
        assert match is not None
        floor = match.group(1)
        assert (
            floor in self.readme_text
        ), f"README should mention the bankstatementparser >= {floor} floor"
