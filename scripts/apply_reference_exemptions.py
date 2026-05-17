#!/usr/bin/env python3
"""
Apply permanent taxonomy exemptions from reference_closure.json.

Only updates rows still on bunpro:auto/* that are listed in taxonomy_exemptions.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
from grammar_reference import TAXONOMY_PATH, exemption_map  # noqa: E402


def main() -> int:
    if not TAXONOMY_PATH.exists():
        raise SystemExit(f"missing taxonomy: {TAXONOMY_PATH}")

    exemptions = exemption_map()
    out_lines: list[str] = []
    attempted = 0
    applied = 0
    skipped: list[str] = []

    for raw in TAXONOMY_PATH.read_text(encoding="utf-8").splitlines():
        if not raw or raw.startswith("#"):
            out_lines.append(raw)
            continue
        row = next(csv.reader([raw], delimiter="\t", quotechar='"'))
        while len(row) < 9:
            row.append("")
        point_slug = row[0].strip()
        bunpro_id = row[3].strip()
        target = exemptions.get(point_slug)
        if target and bunpro_id.startswith("bunpro:auto/"):
            attempted += 1
            row[3] = target
            applied += 1
        elif target and not bunpro_id.startswith("bunpro:auto/"):
            skipped.append(f"{point_slug} (already {bunpro_id})")
        out_lines.append("\t".join(row))

    TAXONOMY_PATH.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    print(f"exemption_targets={len(exemptions)}")
    print(f"attempted={attempted} applied={applied}")
    if skipped:
        print("skipped_already_mapped:")
        for line in skipped:
            print(f"  {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
