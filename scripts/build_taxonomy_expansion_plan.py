#!/usr/bin/env python3
"""
Build a taxonomy expansion plan toward true Bunpro-complete coverage.

Compares live Bunpro slugs (JLPT5–1) against taxonomy + grammar usage and
lists atomic additions needed, plus bucket splits still pending.

Outputs:
  - research-reports/taxonomy_expansion_plan.json
  - research-reports/taxonomy_expansion_plan.md
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
from grammar_reference import (  # noqa: E402
    ROOT,
    load_bunpro_live_points,
    load_reference_closure,
    load_taxonomy_rows,
    normalize_bucket_slugs,
    parse_bunpro_id,
    taxonomy_bunpro_slug_index,
)

OUT_JSON = ROOT / "research-reports/taxonomy_expansion_plan.json"
OUT_MD = ROOT / "research-reports/taxonomy_expansion_plan.md"
GRAMMAR_DIR = ROOT / "grammar-strict"


def grammar_row_counts() -> dict[str, int]:
    counts: dict[str, int] = {}
    for path in GRAMMAR_DIR.rglob("*.tsv"):
        for raw in path.read_text(encoding="utf-8").splitlines():
            if not raw or raw.startswith("#"):
                continue
            row = raw.split("\t")
            if not row:
                continue
            for tag in row[-1].split():
                if tag.startswith("point:"):
                    slug = tag[len("point:") :]
                    counts[slug] = counts.get(slug, 0) + 1
    return counts


def suggest_point_slug(bunpro_slug: str) -> str:
    """Conservative slug for a new taxonomy row."""
    slug = bunpro_slug.strip().lower()
    slug = slug.replace("・", "-").replace("～", "").replace("〜", "")
    slug = slug.replace("/", "-").replace(" ", "-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-") or "bunpro-point"


def main() -> int:
    closure = load_reference_closure()
    levels = closure["primary_reference"]["reverse_coverage_levels"]
    bunpro_points = [p for p in load_bunpro_live_points() if p.get("level") in levels]
    taxonomy_rows = load_taxonomy_rows()
    slug_index = taxonomy_bunpro_slug_index(taxonomy_rows)
    grammar_counts = grammar_row_counts()
    normalize_buckets = normalize_bucket_slugs(closure)
    existing_point_slugs = {r["point_slug"] for r in taxonomy_rows}

    mapping_debt: list[dict[str, str]] = []
    exempt_rows: list[dict[str, str]] = []
    for row in taxonomy_rows:
        status, payload = parse_bunpro_id(row["bunpro_id"])
        if status == "auto":
            mapping_debt.append(row)
        elif status == "exempt":
            exempt_rows.append(row)

    atomic_additions: list[dict[str, Any]] = []
    for point in bunpro_points:
        slug = str(point["slug"])
        if slug in slug_index:
            continue
        proposed = suggest_point_slug(slug)
        while proposed in existing_point_slugs:
            proposed = f"{proposed}-bp"
        atomic_additions.append(
            {
                "bunpro_slug": slug,
                "bunpro_title": point.get("title"),
                "bunpro_level": point.get("level"),
                "proposed_point_slug": proposed,
                "proposed_bunpro_id": f"bunpro:{slug}",
                "action": "add_taxonomy_row_and_grammar_cards",
            }
        )

    atomic_additions.sort(key=lambda x: (x["bunpro_level"], x["bunpro_slug"]))

    bucket_tasks: list[dict[str, Any]] = []
    for row in taxonomy_rows:
        slug = row["point_slug"]
        if slug not in normalize_buckets:
            continue
        status, _ = parse_bunpro_id(row["bunpro_id"])
        bucket_tasks.append(
            {
                "point_slug": slug,
                "module": row["module"],
                "jlpt": row["jlpt"],
                "bunpro_status": status,
                "grammar_rows": grammar_counts.get(slug, 0),
                "action": "split_bucket_to_atomic_bunpro_slugs",
            }
        )

    level_gap = Counter(p["bunpro_level"] for p in atomic_additions)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "bunpro_in_scope_total": len(bunpro_points),
            "taxonomy_rows_total": len(taxonomy_rows),
            "taxonomy_mapped_bunpro_slugs": len(slug_index),
            "atomic_additions_needed": len(atomic_additions),
            "normalize_buckets_pending": len(bucket_tasks),
            "mapping_debt_rows": len(mapping_debt),
            "exempt_rows": len(exempt_rows),
            "atomic_additions_by_level": dict(level_gap),
        },
        "phases": {
            "phase_0_apply_exemptions": {
                "description": "Mark deck-native / content-plan lanes with bunpro:exempt/*",
                "rows": len(exempt_rows),
            },
            "phase_1_split_buckets": {
                "description": "Replace coarse taxonomy buckets with Bunpro-aligned atomic slugs",
                "tasks": bucket_tasks,
            },
            "phase_2_add_atomic_bunpro": {
                "description": "Add taxonomy rows + grammar TSV cards for unmapped Bunpro slugs",
                "total": len(atomic_additions),
                "sample": atomic_additions[:80],
            },
            "phase_3_close_mapping_debt": {
                "description": "Resolve remaining bunpro:auto rows to bunpro:<slug> or exempt",
                "rows": [
                    {
                        "point_slug": r["point_slug"],
                        "module": r["module"],
                        "jlpt": r["jlpt"],
                        "bunpro_id": r["bunpro_id"],
                    }
                    for r in mapping_debt
                ],
            },
        },
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md = [
        "# Taxonomy Expansion Plan",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        "",
        "## Summary",
        "",
        f"- Bunpro JLPT5–1 points: `{payload['summary']['bunpro_in_scope_total']}`",
        f"- Taxonomy rows today: `{payload['summary']['taxonomy_rows_total']}`",
        f"- Distinct Bunpro slugs mapped in taxonomy: `{payload['summary']['taxonomy_mapped_bunpro_slugs']}`",
        f"- **Atomic Bunpro additions needed:** `{payload['summary']['atomic_additions_needed']}`",
        f"- Bucket splits pending: `{payload['summary']['normalize_buckets_pending']}`",
        f"- Mapping debt (auto/missing): `{payload['summary']['mapping_debt_rows']}`",
        f"- Exempt rows: `{payload['summary']['exempt_rows']}`",
        "",
        "## Phase 1 — Split buckets (top)",
        "",
    ]
    for task in bucket_tasks[:25]:
        md.append(
            f"- `{task['point_slug']}` ({task['module']}) status={task['bunpro_status']} "
            f"grammar_rows={task['grammar_rows']}"
        )
    md.extend(["", "## Phase 2 — Atomic additions (sample)", ""])
    for row in atomic_additions[:40]:
        md.append(
            f"- `{row['bunpro_slug']}` ({row['bunpro_level']}) → "
            f"`{row['proposed_point_slug']}`"
        )
    md.append("")
    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print(f"wrote_json={OUT_JSON}")
    print(f"wrote_md={OUT_MD}")
    print(f"atomic_additions_needed={payload['summary']['atomic_additions_needed']}")
    print(f"normalize_buckets_pending={payload['summary']['normalize_buckets_pending']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
