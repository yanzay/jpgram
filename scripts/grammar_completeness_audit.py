#!/usr/bin/env python3
"""
Run the full grammar-completeness audit pipeline.

Steps:
  1) apply_reference_exemptions.py
  2) coverage_audit.py
  3) bunpro_reverse_coverage.py
  4) build_taxonomy_expansion_plan.py
  5) build_remediation_backlog.py
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = Path(__file__).resolve().parent


def run(cmd: list[str]) -> int:
    print("+", " ".join(cmd), flush=True)
    proc = subprocess.run(cmd, cwd=ROOT)
    return proc.returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--skip-bunpro-fetch",
        action="store_true",
        help="Pass through to coverage_audit.py",
    )
    parser.add_argument(
        "--enforce-note-types",
        action="store_true",
        help="Pass through to coverage_audit.py",
    )
    parser.add_argument(
        "--require-full-bunpro-resolution",
        action="store_true",
        help="Pass through to coverage_audit.py",
    )
    parser.add_argument(
        "--min-reverse-coverage-pct",
        type=float,
        default=0.0,
        help="Fail if Bunpro reverse coverage is below this percentage.",
    )
    parser.add_argument(
        "--skip-exemptions",
        action="store_true",
        help="Do not apply reference_closure exemptions.",
    )
    args = parser.parse_args()

    py = sys.executable
    codes: list[int] = []

    if not args.skip_exemptions:
        codes.append(run([py, str(SCRIPTS / "apply_reference_exemptions.py")]))

    coverage_cmd = [py, str(SCRIPTS / "coverage_audit.py")]
    if args.skip_bunpro_fetch:
        coverage_cmd.append("--skip-bunpro-fetch")
    if args.enforce_note_types:
        coverage_cmd.append("--enforce-note-types")
    if args.require_full_bunpro_resolution:
        coverage_cmd.append("--require-full-bunpro-resolution")
    codes.append(run(coverage_cmd))

    codes.append(
        run(
            [
                py,
                str(SCRIPTS / "bunpro_reverse_coverage.py"),
                "--min-coverage-pct",
                str(args.min_reverse_coverage_pct),
            ]
        )
    )
    codes.append(run([py, str(SCRIPTS / "build_taxonomy_expansion_plan.py")]))
    codes.append(run([py, str(SCRIPTS / "build_remediation_backlog.py")]))

    # Exemptions may fix mapping debt even when reverse coverage is still low.
    overall = 0 if all(c == 0 for c in codes) else 2
    print(f"grammar_completeness_audit: exit={overall} step_codes={codes}")
    return overall


if __name__ == "__main__":
    raise SystemExit(main())
