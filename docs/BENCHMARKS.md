# Benchmarks

`benches/bench_detect_and_parse.py` measures what `detect_format` and
`parse_statement` cost on generated MT940, CAMT.053 and CSV statements of
10, 200 and 2,000 entries, plus detection on content that matches no
supported format (the stray file in a folder). It asks two questions:
does detection read the whole document (it should not: the `detect
us/KiB` column should fall as files grow), and is any one format
disproportionately expensive to detect.

Nothing asserts a threshold: wall-clock is not comparable between
machines. CI runs `python benches/bench_detect_and_parse.py --quick` on
every push so the benchmark keeps running against the current API.

## Results

Run with `poetry run python benches/bench_detect_and_parse.py` on
2026-11-27: Apple M1 Pro, macOS 27.2.1, CPython 3.12.16,
bankstatementparser-mcp 0.0.36 with bankstatementparser 0.0.35.
Times are per call; each figure is the tool's own wall-clock, including
the private temp file it writes.

| Format | Entries | KiB | detect ms | parse ms | detect us/KiB |
| :--- | ---: | ---: | ---: | ---: | ---: |
| mt940 | 10 | 0.7 | 5.617 | 22.89 | 8101.2 |
| camt | 10 | 2.9 | 4.991 | 21.13 | 1695.0 |
| csv | 10 | 0.4 | 10.286 | 10.13 | 25504.0 |
| mt940 | 200 | 12.7 | 5.778 | 22.81 | 455.8 |
| camt | 200 | 53.1 | 5.125 | 31.52 | 96.4 |
| csv | 200 | 7.8 | 11.000 | 10.79 | 1404.0 |
| mt940 | 2000 | 131.6 | 7.017 | 40.69 | 53.3 |
| camt | 2000 | 530.5 | 6.605 | 132.78 | 12.5 |
| csv | 2000 | 81.9 | 9.509 | 9.40 | 116.2 |
| unrecognised | 10 | 0.5 | 8.932 | | 18665.6 |
| unrecognised | 200 | 9.9 | 8.788 | | 891.9 |
| unrecognised | 2000 | 100.5 | 10.037 | | 99.9 |

Detection cost stays between 5 and 11 ms whatever the size, so its
per-KiB cost falls by two orders of magnitude from the smallest file to
the largest: detection peeks at the head of the document rather than
reading it in full. Parsing grows with the document (CAMT.053 at 530 KiB
is the most expensive at about 133 ms). Content that matches no format
costs about as much to reject as a CSV costs to detect.

Reproduce with `python benches/bench_detect_and_parse.py` (add `--json`
for machine-readable output).
