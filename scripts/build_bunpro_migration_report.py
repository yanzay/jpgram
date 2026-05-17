#!/usr/bin/env python3
"""
Map legacy grammar/ point tags to the strict Bunpro-atomic taxonomy.

Outputs:
  research-reports/bunpro_migration_report.json
  research-reports/bunpro_migration_report.md
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
from grammar_reference import (  # noqa: E402
    ROOT,
    TAXONOMY_PATH,
    load_taxonomy_rows,
    parse_bunpro_id,
    strict_deck_paths,
)

OUT_JSON = ROOT / "research-reports/bunpro_migration_report.json"
OUT_MD = ROOT / "research-reports/bunpro_migration_report.md"
LEGACY_GRAMMAR = ROOT / "grammar"


def collect_legacy_usage() -> tuple[Counter[str], dict[str, set[str]]]:
    counts: Counter[str] = Counter()
    files: dict[str, set[str]] = defaultdict(set)
    for path in LEGACY_GRAMMAR.rglob("*.tsv"):
        for ln, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not raw or raw.startswith("#"):
                continue
            row = next(csv.reader([raw], delimiter="\t", quotechar='"'))
            tags = row[-1].split() if row else []
            for tag in tags:
                if tag.startswith("point:"):
                    slug = tag[len("point:") :]
                    counts[slug] += 1
                    files[slug].add(f"{path.relative_to(ROOT)}:{ln}")
    return counts, files


def main() -> int:
    strict_taxonomy, _, _ = strict_deck_paths()
    if not strict_taxonomy.exists():
        raise SystemExit(f"run bootstrap first: missing {strict_taxonomy}")

    legacy_rows = {r["point_slug"]: r for r in load_taxonomy_rows(TAXONOMY_PATH)}
    strict_rows = {r["point_slug"]: r for r in load_taxonomy_rows(strict_taxonomy)}
    strict_slugs = set(strict_rows)
    usage, usage_files = collect_legacy_usage()

    legacy_to_bunpro: dict[str, str] = {}
    for slug, row in legacy_rows.items():
        status, bp = parse_bunpro_id(row["bunpro_id"])
        if status == "resolved" and bp:
            legacy_to_bunpro[slug] = bp

    migratable: list[dict[str, Any]] = []
    bucket_debt: list[dict[str, Any]] = []
    exempt_tags: list[dict[str, Any]] = []
    unmapped: list[dict[str, Any]] = []

    for point_slug, row_count in usage.most_common():
        legacy = legacy_rows.get(point_slug, {})
        status, payload = parse_bunpro_id(legacy.get("bunpro_id", ""))
        entry = {
            "legacy_point_slug": point_slug,
            "grammar_rows": row_count,
            "sample_files": sorted(usage_files[point_slug])[:5],
        }
        if status == "exempt" and point_slug in strict_slugs:
            exempt_tags.append({**entry, "strict_point_slug": point_slug, "action": "port_exempt"})
        elif point_slug in strict_slugs:
            migratable.append({**entry, "strict_point_slug": point_slug, "action": "port_identity"})
        elif status == "resolved":
            target = payload
            if target in strict_slugs:
                migratable.append(
                    {
                        **entry,
                        "strict_point_slug": target,
                        "legacy_bunpro_slug": target,
                        "action": "port_retag",
                    }
                )
            else:
                unmapped.append({**entry, "legacy_bunpro_slug": target, "action": "missing_in_strict"})
        elif status == "auto":
            bp = legacy_to_bunpro.get(point_slug)
            bucket_debt.append(
                {
                    **entry,
                    "action": "bucket_needs_split",
                    "legacy_bunpro_id": legacy.get("bunpro_id", ""),
                }
            )
        else:
            unmapped.append({**entry, "action": "no_legacy_taxonomy_row", "legacy_status": status})

    strict_without_cards = sorted(
        slug for slug in strict_slugs if usage.get(slug, 0) == 0 and slug not in usage
    )

    port_rows = sum(x["grammar_rows"] for x in migratable) + sum(x["grammar_rows"] for x in exempt_tags)
    bucket_rows = sum(x["grammar_rows"] for x in bucket_debt)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "legacy_distinct_point_tags": len(usage),
            "strict_taxonomy_rows": len(strict_slugs),
            "migratable_tags": len(migratable) + len(exempt_tags),
            "migratable_grammar_rows": port_rows,
            "bucket_debt_tags": len(bucket_debt),
            "bucket_debt_grammar_rows": bucket_rows,
            "strict_points_without_legacy_cards": len(strict_without_cards),
        },
        "details": {
            "migratable": migratable,
            "exempt_portable": exempt_tags,
            "bucket_debt": bucket_debt,
            "unmapped_legacy_tags": unmapped,
            "strict_without_cards_count": len(strict_without_cards),
            "strict_without_cards_sample": strict_without_cards[:60],
        },
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md = [
        "# Bunpro Migration Report (legacy → strict)",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        "",
        "## Summary",
        "",
        f"- Legacy distinct `point:*` tags: `{payload['summary']['legacy_distinct_point_tags']}`",
        f"- Strict taxonomy rows: `{payload['summary']['strict_taxonomy_rows']}`",
        f"- **Portable tags (auto-port):** `{payload['summary']['migratable_tags']}` "
        f"({payload['summary']['migratable_grammar_rows']} card rows)",
        f"- **Bucket debt tags:** `{payload['summary']['bucket_debt_tags']}` "
        f"({payload['summary']['bucket_debt_grammar_rows']} card rows — need rewrite/split)",
        f"- Strict points still without cards: `{payload['summary']['strict_points_without_legacy_cards']}`",
        "",
        "## Portable mappings (sample)",
        "",
    ]
    for row in migratable[:30]:
        if row.get("action") == "port_retag":
            md.append(
                f"- `{row['legacy_point_slug']}` → `{row['strict_point_slug']}` "
                f"({row['grammar_rows']} rows)"
            )
        else:
            md.append(f"- `{row['legacy_point_slug']}` ({row['grammar_rows']} rows)")
    md.extend(["", "## Bucket debt (sample)", ""])
    for row in bucket_debt[:20]:
        md.append(f"- `{row['legacy_point_slug']}` ({row['grammar_rows']} rows)")
    md.append("")
    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print(f"wrote_json={OUT_JSON}")
    print(f"wrote_md={OUT_MD}")
    print(json.dumps(payload["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
