#!/usr/bin/env python3
"""
Bootstrap the parallel strict Bunpro deck (one-shot setup).

  1. bootstrap_taxonomy_from_bunpro.py
  2. build_bunpro_migration_report.py
  3. port_migratable_cards_to_strict.py
  4. strict_deck_audit.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent


def run(name: str, extra: list[str] | None = None) -> int:
    cmd = [sys.executable, str(SCRIPTS / name)] + (extra or [])
    print("+", " ".join(cmd), flush=True)
    return subprocess.run(cmd, cwd=ROOT).returncode


def main() -> int:
    steps = [
        ("bootstrap_taxonomy_from_bunpro.py", []),
        ("build_bunpro_migration_report.py", []),
        ("port_migratable_cards_to_strict.py", []),
        (
            "strict_deck_audit.py",
            ["--skip-bunpro-fetch", "--require-full-bunpro-resolution"],
        ),
    ]
    codes: list[int] = []
    for script, args in steps:
        codes.append(run(script, args))
    code = 0 if all(c == 0 for c in codes) else 2
    print(f"setup_strict_deck: exit={code} step_codes={codes}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
