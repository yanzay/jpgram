#!/usr/bin/env python3
"""
Bootstrap the strict Bunpro-atomic taxonomy (parallel deck).

Writes data/grammar_taxonomy_bunpro.tsv:
  - one row per in-scope Bunpro slug (JLPT5–1), point_slug == bunpro slug
  - plus permanent exempt rows from reference_closure.json

Does not modify legacy data/grammar_taxonomy.tsv or grammar/.
"""
from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
from grammar_reference import (  # noqa: E402
    ROOT,
    TAXONOMY_PATH,
    exemption_map,
    load_bunpro_live_points,
    load_reference_closure,
    load_taxonomy_rows,
    strict_deck_paths,
)

HEADER = (
    "#columns:point_slug\tjlpt\tmodule\tbunpro_id\ttofugu_url\timabi_url\t"
    "shinkanzen_ref\tdjg_page\tnotes\n"
)


def jlpt_module(level: str) -> tuple[str, str]:
    from grammar_reference import LEVEL_TO_MODULE

    return LEVEL_TO_MODULE.get(level, ("12-beyond-n1", ""))


def load_legacy_exempt_rows() -> dict[str, dict[str, str]]:
    if not TAXONOMY_PATH.exists():
        return {}
    legacy = {r["point_slug"]: r for r in load_taxonomy_rows(TAXONOMY_PATH)}
    out: dict[str, dict[str, str]] = {}
    for slug, target in exemption_map().items():
        if slug in legacy:
            row = dict(legacy[slug])
            row["bunpro_id"] = target
            out[slug] = row
    return out


def main() -> int:
    closure = load_reference_closure()
    strict_taxonomy, _, manifest_path = strict_deck_paths(closure)
    levels = closure["primary_reference"]["reverse_coverage_levels"]
    exemptions = exemption_map(closure)
    legacy_exempt = load_legacy_exempt_rows()

    bunpro_rows: list[dict[str, str]] = []
    for point in load_bunpro_live_points():
        level = str(point.get("level", ""))
        if level not in levels:
            continue
        slug = str(point["slug"]).strip()
        module, jlpt = jlpt_module(level)
        bunpro_rows.append(
            {
                "point_slug": slug,
                "jlpt": jlpt,
                "module": module,
                "bunpro_id": f"bunpro:{slug}",
                "tofugu_url": "",
                "imabi_url": "",
                "shinkanzen_ref": f"sk:auto/{jlpt}" if jlpt else "sk:auto/unknown",
                "djg_page": f"djg:bunpro/{slug}",
                "notes": (
                    f"strict-deck; bunpro:{slug}; "
                    f"{point.get('title', '')}; {point.get('meaning', '')}"
                ).strip(),
            }
        )

    bunpro_rows.sort(key=lambda r: (r["module"], r["point_slug"]))

    exempt_rows: list[dict[str, str]] = []
    for slug, exempt_id in sorted(exemptions.items()):
        reason = exempt_id.split("exempt/", 1)[-1] if "exempt/" in exempt_id else exempt_id
        from grammar_reference import EXEMPT_MODULE

        module, jlpt = EXEMPT_MODULE.get(reason, ("12-beyond-n1", ""))
        if slug in legacy_exempt:
            row = legacy_exempt[slug]
        else:
            row = {
                "point_slug": slug,
                "jlpt": jlpt,
                "module": module,
                "bunpro_id": exempt_id,
                "tofugu_url": "",
                "imabi_url": "",
                "shinkanzen_ref": "sk:exempt",
                "djg_page": f"djg:exempt/{slug}",
                "notes": f"strict-deck exempt; {reason}",
            }
        exempt_rows.append(row)

    all_rows = bunpro_rows + exempt_rows
    lines = [HEADER]
    for row in all_rows:
        lines.append(
            "\t".join(
                [
                    row["point_slug"],
                    row["jlpt"],
                    row["module"],
                    row["bunpro_id"],
                    row["tofugu_url"],
                    row["imabi_url"],
                    row["shinkanzen_ref"],
                    row["djg_page"],
                    row["notes"],
                ]
            )
        )

    strict_taxonomy.parent.mkdir(parents=True, exist_ok=True)
    strict_taxonomy.write_text("\n".join(lines) + "\n", encoding="utf-8")

    manifest: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "taxonomy_path": str(strict_taxonomy.relative_to(ROOT)),
        "grammar_dir": closure["strict_deck"]["grammar_dir"],
        "counts": {
            "bunpro_atomic_rows": len(bunpro_rows),
            "exempt_rows": len(exempt_rows),
            "total_rows": len(all_rows),
        },
        "in_scope_levels": levels,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"wrote_taxonomy={strict_taxonomy}")
    print(f"bunpro_rows={len(bunpro_rows)} exempt_rows={len(exempt_rows)} total={len(all_rows)}")
    print(f"wrote_manifest={manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
