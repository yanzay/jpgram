#!/usr/bin/env python3
"""
Validate pitch-accent index coverage gates.

Usage:
  python validate_pitchaccent_coverage.py \
    --min-coverage 8 \
    --min-weighted-coverage 15 \
    --max-conflicts 1000
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

INDEX_PATH = Path("media/pitchaccent_index.json")


def main() -> int:
    ap = argparse.ArgumentParser(description="Pitch-accent coverage gate")
    ap.add_argument("--min-coverage", type=float, default=0.0)
    ap.add_argument("--min-weighted-coverage", type=float, default=0.0)
    ap.add_argument("--max-conflicts", type=int, default=-1)
    ap.add_argument("--min-lexical-coverage", type=float, default=0.0)
    ap.add_argument("--min-lexical-weighted-coverage", type=float, default=0.0)
    args = ap.parse_args()

    if not INDEX_PATH.exists():
        print(f"✗ missing {INDEX_PATH}; run build_pitchaccent.py first")
        return 2

    data = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    cov = float(data.get("coverage_percent", 0.0))
    wcov = float(data.get("weighted_coverage_percent", 0.0))
    lcov = float(data.get("lexical_coverage_percent", 0.0))
    lwcov = float(data.get("lexical_weighted_coverage_percent", 0.0))
    conflicts = int(data.get("conflicts_count", 0))
    missing = int(data.get("missing_count", 0))
    entries = len(data.get("entries", {}))

    print(
        f"Pitch index: entries={entries} coverage={cov:.2f}% "
        f"weighted={wcov:.2f}% lexical={lcov:.2f}%/{lwcov:.2f}% "
        f"conflicts={conflicts} missing={missing}"
    )

    if cov < args.min_coverage:
        print(f"✗ coverage gate failed: {cov:.2f}% < {args.min_coverage:.2f}%")
        return 3
    if wcov < args.min_weighted_coverage:
        print(f"✗ weighted coverage gate failed: {wcov:.2f}% < {args.min_weighted_coverage:.2f}%")
        return 4
    if args.max_conflicts >= 0 and conflicts > args.max_conflicts:
        print(f"✗ conflict gate failed: {conflicts} > {args.max_conflicts}")
        return 5
    if lcov < args.min_lexical_coverage:
        print(f"✗ lexical coverage gate failed: {lcov:.2f}% < {args.min_lexical_coverage:.2f}%")
        return 6
    if lwcov < args.min_lexical_weighted_coverage:
        print(
            f"✗ lexical weighted coverage gate failed: {lwcov:.2f}% "
            f"< {args.min_lexical_weighted_coverage:.2f}%"
        )
        return 7

    print("✓ pitch-accent coverage gates passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
