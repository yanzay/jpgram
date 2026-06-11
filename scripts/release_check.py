#!/usr/bin/env python3
"""Run the full non-destructive premium release gate."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = Path("/tmp/jpgram-release-check.apkg")


def run(argv: list[str]) -> None:
    print(f"\n==> {' '.join(argv)}")
    subprocess.check_call(argv, cwd=ROOT)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run all premium release checks without committing.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Temporary APKG output path")
    args = parser.parse_args()

    py = sys.executable
    run([py, "validate_anki_data.py"])
    run([py, "validate_content_quality.py", "--strict"])
    run([py, "validate_grammar_taxonomy.py"])
    run([py, "validate_pitchaccent_coverage.py"])
    run([
        py,
        "scripts/strict_deck_audit.py",
        "--skip-bunpro-fetch",
        "--enforce-note-types",
        "--require-full-bunpro-resolution",
        "--min-reverse-coverage-pct",
        "100",
    ])
    run([py, "-m", "pytest", "-q"])
    run([py, "build_anki_package.py", "--out", str(args.out)])
    run([py, "validate_apkg.py", str(args.out)])

    print(f"\nPremium release check passed: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
