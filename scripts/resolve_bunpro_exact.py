#!/usr/bin/env python3
"""
Resolve exact bunpro:auto/<slug> mappings against live Bunpro snapshot.

This is intentionally conservative:
- Only upgrades rows where `<slug>` exactly matches a live Bunpro slug.
- Leaves all other rows untouched for manual curation.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
TAXONOMY_PATH = ROOT / "data/grammar_taxonomy.tsv"
BUNPRO_LIVE_PATH = ROOT / "data/grammar-refs/bunpro_live_index.json"


def main() -> int:
    if not TAXONOMY_PATH.exists():
        raise SystemExit(f"missing taxonomy: {TAXONOMY_PATH}")
    if not BUNPRO_LIVE_PATH.exists():
        raise SystemExit(f"missing Bunpro live snapshot: {BUNPRO_LIVE_PATH}")

    bunpro = json.loads(BUNPRO_LIVE_PATH.read_text(encoding="utf-8"))
    bunpro_slugs = {p["slug"] for p in bunpro.get("points", [])}

    out_lines: list[str] = []
    changed = 0
    total_auto = 0

    for raw in TAXONOMY_PATH.read_text(encoding="utf-8").splitlines():
        if not raw:
            out_lines.append(raw)
            continue
        if raw.startswith("#"):
            out_lines.append(raw)
            continue

        row = next(csv.reader([raw], delimiter="\t", quotechar='"'))
        while len(row) < 9:
            row.append("")
        bunpro_id = row[3].strip()
        if bunpro_id.startswith("bunpro:auto/"):
            total_auto += 1
            candidate = bunpro_id.split("bunpro:auto/", 1)[1].strip()
            if candidate in bunpro_slugs:
                row[3] = f"bunpro:{candidate}"
                changed += 1

        out_lines.append("\t".join(row))

    TAXONOMY_PATH.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    print(f"auto_rows={total_auto}")
    print(f"resolved_exact={changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
