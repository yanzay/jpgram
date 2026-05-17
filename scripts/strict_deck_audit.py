#!/usr/bin/env python3
"""Run coverage + reverse audits against the strict Bunpro-atomic deck."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = Path(__file__).resolve().parent


def run(cmd: list[str]) -> int:
    print("+", " ".join(cmd), flush=True)
    return subprocess.run(cmd, cwd=ROOT).returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-bunpro-fetch", action="store_true")
    parser.add_argument("--enforce-note-types", action="store_true")
    parser.add_argument("--require-full-bunpro-resolution", action="store_true")
    parser.add_argument(
        "--min-reverse-coverage-pct",
        type=float,
        default=0.0,
    )
    args = parser.parse_args()
    py = sys.executable
    tax = "data/grammar_taxonomy_bunpro.tsv"
    gram = "grammar-strict"

    cov = [
        py,
        str(SCRIPTS / "coverage_audit.py"),
        "--taxonomy",
        tax,
        "--grammar-dir",
        gram,
        "--report-json",
        "research-reports/strict_coverage_audit_report.json",
        "--report-md",
        "research-reports/strict_coverage_audit_report.md",
    ]
    if args.skip_bunpro_fetch:
        cov.append("--skip-bunpro-fetch")
    cov.append("--allow-partial-point-usage")
    if args.enforce_note_types:
        cov.append("--enforce-note-types")
    if args.require_full_bunpro_resolution:
        cov.append("--require-full-bunpro-resolution")

    rev = [
        py,
        str(SCRIPTS / "bunpro_reverse_coverage.py"),
        "--taxonomy",
        tax,
        "--grammar-dir",
        gram,
        "--min-coverage-pct",
        str(args.min_reverse_coverage_pct),
        "--report-json",
        "research-reports/strict_bunpro_reverse_coverage_report.json",
        "--report-md",
        "research-reports/strict_bunpro_reverse_coverage_report.md",
    ]

    codes = [run(cov), run(rev)]
    code = 0 if all(c == 0 for c in codes) else 2
    print(f"strict_deck_audit: exit={code} codes={codes}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
