#!/usr/bin/env python3
"""
Build a prioritized remediation backlog from coverage audit artifacts.

Inputs:
  - research-reports/coverage_audit_report.json
  - data/grammar_taxonomy.tsv

Outputs:
  - research-reports/coverage_remediation_backlog.json
  - research-reports/coverage_remediation_backlog.md
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
AUDIT_PATH = ROOT / "research-reports/coverage_audit_report.json"
TAXONOMY_PATH = ROOT / "data/grammar_taxonomy.tsv"
OUT_JSON = ROOT / "research-reports/coverage_remediation_backlog.json"
OUT_MD = ROOT / "research-reports/coverage_remediation_backlog.md"

BUCKET_RE = re.compile(
    r"(misc|family|basics|core|others?|set-phrases|constructions|extensions|style|slang|jargon|phrases)$"
)


def load_taxonomy() -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    for raw in TAXONOMY_PATH.read_text(encoding="utf-8").splitlines():
        if not raw or raw.startswith("#"):
            continue
        row = next(csv.reader([raw], delimiter="\t", quotechar='"'))
        while len(row) < 9:
            row.append("")
        point_slug = row[0].strip()
        rows[point_slug] = {
            "point_slug": point_slug,
            "jlpt": row[1].strip(),
            "module": row[2].strip(),
            "bunpro_id": row[3].strip(),
        }
    return rows


def bunpro_status(bunpro_id: str) -> str:
    value = bunpro_id.strip()
    if not value:
        return "missing"
    if value.startswith("bunpro:auto/"):
        return "auto"
    if value.startswith("bunpro:"):
        payload = value.split("bunpro:", 1)[1].strip()
        return "resolved" if payload else "malformed"
    return "malformed"


def jlpt_priority(jlpt: str) -> int:
    order = {"n5": 5, "n4": 4, "n3": 3, "n2": 2, "n1": 1, "beyond": 0}
    return order.get(jlpt.lower(), 0)


def module_priority(module: str) -> int:
    m = re.match(r"^(\d{2})-", module)
    return int(m.group(1)) if m else 99


def note_type_suggestion(existing: list[str]) -> str:
    s = set(existing)
    if s == {"contrast"}:
        return "Add recognition first, then production."
    if s == {"cloze"}:
        return "Add recognition first, then contrast."
    if s == {"recognition"}:
        return "Add production first, then cloze."
    if s == {"production"}:
        return "Add recognition first, then contrast."
    if s == {"listening"} or s == {"dictation"}:
        return "Add recognition + production to link form to meaning."
    return "Add one high-utility type (recognition/production) to reach >=2 types."


def main() -> int:
    if not AUDIT_PATH.exists():
        raise SystemExit(f"missing audit report: {AUDIT_PATH}")
    if not TAXONOMY_PATH.exists():
        raise SystemExit(f"missing taxonomy: {TAXONOMY_PATH}")

    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    taxonomy = load_taxonomy()

    sparse_note_types = audit["details"].get("sparse_note_types", [])
    unresolved_bunpro = []
    for point_slug, row in taxonomy.items():
        status = bunpro_status(row["bunpro_id"])
        if status in {"auto", "missing", "malformed"}:
            bucket_like = bool(BUCKET_RE.search(point_slug))
            unresolved_bunpro.append(
                {
                    "point_slug": point_slug,
                    "module": row["module"],
                    "jlpt": row["jlpt"],
                    "bunpro_status": status,
                    "bunpro_id": row["bunpro_id"],
                    "bucket_like_slug": bucket_like,
                    "lane": "taxonomy-normalization" if bucket_like else "bunpro-mapping",
                    "priority_score": (
                        jlpt_priority(row["jlpt"]) * 10
                        + (3 if bucket_like else 0)
                        + (20 - min(module_priority(row["module"]), 20))
                    ),
                }
            )

    unresolved_bunpro.sort(
        key=lambda x: (
            0 if x["lane"] == "taxonomy-normalization" else 1,
            -x["priority_score"],
            x["module"],
            x["point_slug"],
        )
    )

    note_type_tasks = []
    for row in sparse_note_types:
        point = row["point_slug"]
        t = taxonomy.get(point, {})
        note_type_tasks.append(
            {
                "point_slug": point,
                "module": (t.get("module") or (row.get("modules") or [""])[0]),
                "jlpt": t.get("jlpt", ""),
                "note_type_count": row["note_type_count"],
                "note_types": row["note_types"],
                "rows": row["rows"],
                "unique_sentences": row["unique_sentences"],
                "suggested_action": note_type_suggestion(row["note_types"]),
                "priority_score": (
                    jlpt_priority(t.get("jlpt", "")) * 10
                    + min(int(row["rows"]), 30)
                    + (20 - min(module_priority(t.get("module", "")), 20))
                ),
            }
        )

    note_type_tasks.sort(
        key=lambda x: (
            -x["priority_score"],
            x["module"],
            x["point_slug"],
        )
    )

    module_unresolved = Counter(item["module"] for item in unresolved_bunpro)
    module_note_types = Counter(item["module"] for item in note_type_tasks)
    lane_counts = Counter(item["lane"] for item in unresolved_bunpro)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_audit_report": str(AUDIT_PATH.relative_to(ROOT)),
        "summary": {
            "unresolved_bunpro_total": len(unresolved_bunpro),
            "unresolved_bunpro_by_lane": dict(lane_counts),
            "single_note_type_total": len(note_type_tasks),
            "module_unresolved_counts": dict(module_unresolved),
            "module_note_type_counts": dict(module_note_types),
        },
        "priorities": {
            "bunpro_unresolved": unresolved_bunpro,
            "note_type_expansion": note_type_tasks,
        },
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md_lines = [
        "# Coverage Remediation Backlog",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Source audit: `{payload['source_audit_report']}`",
        "",
        "## Summary",
        "",
        f"- Unresolved Bunpro mappings: `{payload['summary']['unresolved_bunpro_total']}`",
        f"- Unresolved lane split: `{json.dumps(payload['summary']['unresolved_bunpro_by_lane'], ensure_ascii=False)}`",
        f"- Single-note-type points: `{payload['summary']['single_note_type_total']}`",
        "",
        "## Top Bunpro Mapping Tasks",
        "",
    ]
    for item in unresolved_bunpro[:40]:
        md_lines.append(
            f"- `{item['point_slug']}` ({item['module']}, {item['jlpt'] or 'n?'}) "
            f"[{item['lane']}] status={item['bunpro_status']}"
        )

    md_lines.extend(["", "## Top Note-Type Expansion Tasks", ""])
    for item in note_type_tasks[:40]:
        md_lines.append(
            f"- `{item['point_slug']}` ({item['module']}, {item['jlpt'] or 'n?'}) "
            f"types={','.join(item['note_types'])} rows={item['rows']} -> {item['suggested_action']}"
        )
    md_lines.append("")

    OUT_MD.write_text("\n".join(md_lines), encoding="utf-8")

    print(f"wrote_json={OUT_JSON}")
    print(f"wrote_md={OUT_MD}")
    print(f"unresolved_bunpro={len(unresolved_bunpro)}")
    print(f"single_note_type={len(note_type_tasks)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
