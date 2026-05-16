#!/usr/bin/env python3
"""
Validate grammar point taxonomy coverage against shipped TSV tags.

Checks:
  - data/grammar_taxonomy.tsv exists and is non-empty
  - point_slug column has no duplicates
  - every point:* tag used in grammar TSVs exists in taxonomy
  - coarse module-level point tags (point:module-*) are rejected
"""
from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

GRAMMAR_DIR = Path("grammar")
TAXONOMY_PATH = Path("data/grammar_taxonomy.tsv")


def load_taxonomy_points() -> tuple[set[str], list[str]]:
    if not TAXONOMY_PATH.exists():
        return set(), [f"missing {TAXONOMY_PATH}"]
    points: list[str] = []
    for raw in TAXONOMY_PATH.read_text(encoding="utf-8").splitlines():
        if not raw or raw.startswith("#"):
            continue
        row = next(csv.reader([raw], delimiter="\t", quotechar='"'))
        if row and row[0].strip():
            points.append(row[0].strip())
    errs: list[str] = []
    if not points:
        errs.append(f"{TAXONOMY_PATH}: no taxonomy rows")
    dupes = [p for p, n in Counter(points).items() if n > 1]
    for p in sorted(dupes):
        errs.append(f"{TAXONOMY_PATH}: duplicate point_slug '{p}'")
    return set(points), errs


def collect_points_from_grammar() -> tuple[set[str], list[str]]:
    used: set[str] = set()
    errs: list[str] = []
    for path in sorted(GRAMMAR_DIR.rglob("*.tsv")):
        for ln, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not raw or raw.startswith("#"):
                continue
            row = next(csv.reader([raw], delimiter="\t", quotechar='"'))
            if not row:
                continue
            tags = row[-1].split()
            points = [t[len("point:"):] for t in tags if t.startswith("point:")]
            if not points:
                errs.append(f"{path}:{ln}: missing point:* tag")
                continue
            for p in points:
                if p.startswith("module-"):
                    errs.append(f"{path}:{ln}: coarse point tag '{p}' is not allowed")
                used.add(p)
    return used, errs


def main() -> int:
    taxonomy_points, errs = load_taxonomy_points()
    used_points, usage_errs = collect_points_from_grammar()
    errs.extend(usage_errs)
    for p in sorted(used_points):
        if p not in taxonomy_points:
            errs.append(f"point '{p}' used in grammar/ but missing in {TAXONOMY_PATH}")
    if errs:
        for e in errs:
            print(e)
        print(f"\n✗ taxonomy validation failed ({len(errs)} issue(s))")
        return 1
    print(
        f"✓ taxonomy validation passed: {len(used_points)} used points mapped in "
        f"{TAXONOMY_PATH}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

