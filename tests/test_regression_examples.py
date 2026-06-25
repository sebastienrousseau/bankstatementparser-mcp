# Copyright (C) 2023-2026 Bank Statement Parser. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0

"""Regression suite: execute every shipped example script end-to-end.

Each example under ``examples/`` is discovered automatically and run as
a real subprocess with ``sys.executable``, exactly as a user would run
it. A script that crashes, prints an error, or drifts away from the
current public API fails the suite. The examples are self-contained
(inline fixtures, no network, no files outside a tempdir), so no extra
arguments or fixtures are required.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = REPO_ROOT / "examples"


def _discover_examples() -> list[Path]:
    """Return every runnable ``examples/*.py`` script, sorted by name."""
    return sorted(
        py for py in EXAMPLES_DIR.glob("*.py") if "__pycache__" not in str(py)
    )


EXAMPLE_SCRIPTS = _discover_examples()


def _run_example(script: Path, timeout: int = 180) -> str:
    """Run one example as a subprocess and return its stdout.

    Args:
        script: The example script to execute.
        timeout: Seconds to allow before failing.

    Returns:
        The captured stdout of the script.
    """
    env = os.environ.copy()
    env["PATH"] = (
        str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
    )
    proc = subprocess.run(
        [sys.executable, str(script)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
    )
    assert proc.returncode == 0, (
        f"{script.relative_to(REPO_ROOT)} exited {proc.returncode}\n"
        f"--- stdout ---\n{proc.stdout}\n--- stderr ---\n{proc.stderr}"
    )
    return proc.stdout


def test_examples_discovered() -> None:
    """Every ``examples/*.py`` on disk is in the regressed set.

    Guards against an example being silently dropped from the suite:
    the discovered set must equal the on-disk set exactly (no skips),
    and there must be at least one to regress against.
    """
    assert EXAMPLE_SCRIPTS, "no examples/*.py scripts discovered"
    on_disk = {
        py for py in EXAMPLES_DIR.glob("*.py") if "__pycache__" not in str(py)
    }
    assert set(EXAMPLE_SCRIPTS) == on_disk, (
        "discovered example set drifted from on-disk *.py files: "
        f"missing={sorted(p.name for p in on_disk - set(EXAMPLE_SCRIPTS))} "
        f"extra={sorted(p.name for p in set(EXAMPLE_SCRIPTS) - on_disk)}"
    )


@pytest.mark.parametrize(
    "script",
    EXAMPLE_SCRIPTS,
    ids=[p.name for p in EXAMPLE_SCRIPTS],
)
def test_example_runs_clean(script: Path) -> None:
    """Every example exits 0 and prints something."""
    out = _run_example(script)
    assert out.strip(), f"{script.name} produced no output"
