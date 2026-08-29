#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""What format detection and parsing cost across six statement formats.

This server accepts a statement in any of six formats and works out which
one it is. An agent walking a folder calls ``detect_format`` on every file,
often only to decide whether to bother parsing it — so detection is on the
hot path in a way parsing is not.

Two questions follow, and neither had an answer:

* **Does detection read the whole document?** It should not: a format is
  identifiable from its first few lines. If ``detect_format`` cost tracks
  file size, every skipped file is being read in full to be skipped. Read
  the ``detect us/KiB`` column — it should *fall* as files grow, because a
  fixed-size peek amortises. Flat means the whole file is being consumed.

* **Is any one format disproportionately expensive?** The formats differ —
  XML costs more than a flat text ledger — but a large gap in *detection*
  is suspicious, because detection should be doing roughly the same small
  amount of work whatever the format.

Detection is also measured on the **wrong-format** case: content that
resembles nothing supported. That is what a folder of stray files produces,
and a detector that is slowest when it fails is slowest exactly where a
directory walk spends its time.

Run::

    python benches/bench_detect_and_parse.py
    python benches/bench_detect_and_parse.py --json
    python benches/bench_detect_and_parse.py --quick     # what CI runs

Nothing here asserts a threshold: wall-clock is not comparable between
machines, and a flaky performance gate teaches people to ignore red. CI
runs ``--quick`` so a benchmark that has stopped compiling against the
current API fails the build instead of rotting into a file that reads as
verified and is not.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bankstatementparser_mcp import server  # noqa: E402

MT940_HEAD = """:20:STMT-BENCH
:25:COBADEFFXXX/DE89370400440532013000
:28C:42/1
:60F:C260620EUR1000,00
"""
MT940_TXN = """:61:2606210621CR{amount},00NMSCREF{i}//CREF{i}
:86:Benchmark entry {i}
"""
MT940_TAIL = ":62F:C260621EUR2000,00\n"

CAMT_HEAD = """<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.053.001.08">
 <BkToCstmrStmt>
  <GrpHdr><MsgId>BENCH</MsgId><CreDtTm>2026-06-21T10:00:00</CreDtTm></GrpHdr>
  <Stmt><Id>STMT-1</Id>
   <Acct><Id><IBAN>DE89370400440532013000</IBAN></Id></Acct>
"""
CAMT_NTRY = """   <Ntry><Amt Ccy="EUR">{amount}.00</Amt><CdtDbtInd>CRDT</CdtDbtInd>
    <Sts><Cd>BOOK</Cd></Sts><BookgDt><Dt>2026-06-21</Dt></BookgDt>
    <ValDt><Dt>2026-06-21</Dt></ValDt>
    <NtryDtls><TxDtls><Refs><EndToEndId>E2E-{i}</EndToEndId></Refs>
     </TxDtls></NtryDtls></Ntry>
"""
CAMT_TAIL = "  </Stmt>\n </BkToCstmrStmt>\n</Document>\n"

CSV_HEAD = "date,amount,currency,description,reference\n"
CSV_ROW = "2026-06-21,{amount}.00,EUR,Payment {i},REF{i}\n"


def build(fmt: str, entries: int) -> str:
    """A statement of ``entries`` transactions in the requested format."""
    if fmt == "mt940":
        body = "".join(
            MT940_TXN.format(amount=(i % 900) + 100, i=i)
            for i in range(entries)
        )
        return MT940_HEAD + body + MT940_TAIL
    if fmt == "camt":
        body = "".join(
            CAMT_NTRY.format(amount=(i % 900) + 100, i=i)
            for i in range(entries)
        )
        return CAMT_HEAD + body + CAMT_TAIL
    if fmt == "csv":
        body = "".join(
            CSV_ROW.format(amount=(i % 900) + 100, i=i) for i in range(entries)
        )
        return CSV_HEAD + body
    raise ValueError(f"no builder for {fmt!r}")


def build_unrecognised(entries: int) -> str:
    """Content resembling no supported format — a stray file in a folder."""
    return "".join(
        f"line {i}: nothing here looks like a bank statement\n"
        for i in range(entries)
    )


def _best(call, repeats: int) -> float:
    """Best-of timing after one untimed warm-up.

    The minimum is the least noisy estimator available; the mean follows
    whatever else the machine is doing.
    """
    call()
    samples = []
    for _ in range(repeats):
        start = time.perf_counter()
        call()
        samples.append(time.perf_counter() - start)
    return min(samples)


def _safe(call):
    """Run a tool, treating a refusal as a result rather than an error.

    How fast a tool rejects input is as much a measurement as how fast it
    accepts it, and a folder walk meets far more rejections.
    """

    def wrapped():
        try:
            return call()
        except Exception:
            return None

    return wrapped


def measure(fmt: str, entries: int, repeats: int) -> dict:
    text = build(fmt, entries)
    kib = len(text) / 1024
    detect = _best(_safe(lambda: server.detect_format(text)), repeats)
    parse = _best(_safe(lambda: server.parse_statement(text)), repeats)
    return {
        "format": fmt,
        "entries": entries,
        "kib": kib,
        "detect_ms": detect * 1e3,
        "parse_ms": parse * 1e3,
        "detect_us_per_kib": detect * 1e6 / kib if kib else 0.0,
        "detect_share": detect / parse if parse else 0.0,
    }


def measure_unrecognised(entries: int, repeats: int) -> dict:
    text = build_unrecognised(entries)
    kib = len(text) / 1024
    detect = _best(_safe(lambda: server.detect_format(text)), repeats)
    return {
        "format": "unrecognised",
        "entries": entries,
        "kib": kib,
        "detect_ms": detect * 1e3,
        "detect_us_per_kib": detect * 1e6 / kib if kib else 0.0,
    }


def run(quick: bool) -> dict:
    sizes = [10, 200] if quick else [10, 200, 2_000]
    repeats = 3 if quick else 7
    formats = ["mt940", "camt", "csv"]
    return {
        "rows": [measure(f, n, repeats) for n in sizes for f in formats],
        "unrecognised": [measure_unrecognised(n, repeats) for n in sizes],
    }


def render(results: dict) -> None:
    print(
        f"{'format':>14}{'entries':>9}{'KiB':>9}{'detect ms':>11}"
        f"{'parse ms':>10}{'detect us/KiB':>15}"
    )
    for row in results["rows"]:
        print(
            f"{row['format']:>14}{row['entries']:>9}{row['kib']:>9.1f}"
            f"{row['detect_ms']:>11.3f}{row['parse_ms']:>10.2f}"
            f"{row['detect_us_per_kib']:>15.1f}"
        )
    print("\n  unrecognised content — the stray file in a folder")
    for row in results["unrecognised"]:
        print(
            f"{row['format']:>14}{row['entries']:>9}{row['kib']:>9.1f}"
            f"{row['detect_ms']:>11.3f}{'':>10}"
            f"{row['detect_us_per_kib']:>15.1f}"
        )

    by_format: dict[str, list[dict]] = {}
    for row in results["rows"]:
        by_format.setdefault(row["format"], []).append(row)
    print()
    for fmt, rows in by_format.items():
        if len(rows) < 2 or not rows[0]["detect_us_per_kib"]:
            continue
        drift = rows[-1]["detect_us_per_kib"] / rows[0]["detect_us_per_kib"]
        verdict = (
            "peeks at the head" if drift < 0.5 else "reads the whole file"
        )
        # Two decimals renders a strong result as "0.00x", which reads as
        # a broken measurement rather than as a detector that barely looks
        # at the file.
        shown = f"{drift:.2f}" if drift >= 0.01 else f"{drift:.4f}"
        print(
            f"  {fmt:>8}: detect us/KiB at {rows[-1]['kib']:,.0f} KiB is "
            f"{shown}x the cost at {rows[0]['kib']:,.1f} KiB "
            f"— {verdict}."
        )
    print(
        "\n  Falling us/KiB means a fixed-size peek amortising, which is\n"
        "  what you want: a folder walk skips a file without reading it.\n"
        "  Flat means every skipped file is being consumed in full."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument(
        "--quick", action="store_true", help="small sizes, as CI runs"
    )
    args = parser.parse_args()

    results = run(quick=args.quick)
    if args.json:
        json.dump(results, sys.stdout, indent=1)
        print()
    else:
        render(results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
