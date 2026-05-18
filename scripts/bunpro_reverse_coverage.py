#!/usr/bin/env python3
"""
Reverse grammar coverage audit: Bunpro live checklist -> deck.

For each in-scope Bunpro slug, verify:
  - at least one taxonomy row maps to it (resolved, not auto)
  - at least one grammar TSV uses a point tag that maps to that slug

Outputs:
  - research-reports/bunpro_reverse_coverage_report.json
  - research-reports/bunpro_reverse_coverage_report.md
"""
from __future__ import annotations

import argparse
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
    parse_bunpro_id,
    taxonomy_bunpro_slug_index,
)

REPORT_JSON = ROOT / "research-reports/bunpro_reverse_coverage_report.json"
REPORT_MD = ROOT / "research-reports/bunpro_reverse_coverage_report.md"
GRAMMAR_DIR = ROOT / "grammar-strict"
TAXONOMY_PATH: Path = ROOT / "data/grammar_taxonomy_bunpro.tsv"


def configure_paths(
    *,
    taxonomy: Path | None = None,
    grammar_dir: Path | None = None,
    report_json: Path | None = None,
    report_md: Path | None = None,
) -> None:
    global GRAMMAR_DIR, TAXONOMY_PATH, REPORT_JSON, REPORT_MD
    if grammar_dir is not None:
        GRAMMAR_DIR = grammar_dir
    if taxonomy is not None:
        TAXONOMY_PATH = taxonomy
    if report_json is not None:
        REPORT_JSON = report_json
    if report_md is not None:
        REPORT_MD = report_md


def collect_point_usage() -> dict[str, int]:
    usage: dict[str, int] = {}
    for path in GRAMMAR_DIR.rglob("*.tsv"):
        for raw in path.read_text(encoding="utf-8").splitlines():
            if not raw or raw.startswith("#"):
                continue
            row = raw.split("\t")
            if not row:
                continue
            tags = row[-1].split()
            for tag in tags:
                if tag.startswith("point:"):
                    slug = tag[len("point:") :]
                    usage[slug] = usage.get(slug, 0) + 1
    return usage


def point_slug_to_bunpro_slug(taxonomy_rows: list[dict[str, str]]) -> dict[str, str]:
    out: dict[str, str] = {}
    for row in taxonomy_rows:
        status, slug = parse_bunpro_id(row["bunpro_id"])
        if status == "resolved" and slug:
            out[row["point_slug"]] = slug
    return out


def build_report(min_coverage_pct: float) -> dict[str, Any]:
    closure = load_reference_closure()
    levels = closure["primary_reference"]["reverse_coverage_levels"]
    bunpro_points = load_bunpro_live_points()
    taxonomy_rows = load_taxonomy_rows(TAXONOMY_PATH)
    usage = collect_point_usage()
    slug_index = taxonomy_bunpro_slug_index(taxonomy_rows)
    point_to_bunpro = point_slug_to_bunpro_slug(taxonomy_rows)

    in_scope = [p for p in bunpro_points if p.get("level") in levels]
    covered: list[dict[str, Any]] = []
    missing_taxonomy: list[dict[str, Any]] = []
    missing_grammar: list[dict[str, Any]] = []

    for point in in_scope:
        slug = str(point["slug"])
        tax_slugs = slug_index.get(slug, [])
        grammar_hits = [
            ts
            for ts in tax_slugs
            if usage.get(ts, 0) > 0
        ]
        entry = {
            "bunpro_slug": slug,
            "bunpro_title": point.get("title"),
            "bunpro_level": point.get("level"),
            "taxonomy_point_slugs": tax_slugs,
            "grammar_point_slugs": grammar_hits,
        }
        if not tax_slugs:
            missing_taxonomy.append(entry)
        elif not grammar_hits:
            missing_grammar.append(entry)
        else:
            covered.append(entry)

    total = len(in_scope)
    covered_total = len(covered)
    coverage_pct = round((covered_total / total) * 100, 2) if total else 0.0
    by_level: dict[str, dict[str, int]] = {}
    for point in in_scope:
        level = str(point.get("level", ""))
        slug = str(point["slug"])
        bucket = by_level.setdefault(
            level, {"total": 0, "covered": 0, "missing_taxonomy": 0, "missing_grammar": 0}
        )
        bucket["total"] += 1
        if slug in {c["bunpro_slug"] for c in covered}:
            bucket["covered"] += 1
        elif slug in {m["bunpro_slug"] for m in missing_taxonomy}:
            bucket["missing_taxonomy"] += 1
        else:
            bucket["missing_grammar"] += 1

    pass_gate = coverage_pct >= min_coverage_pct

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "reference_closure": str(
            (ROOT / closure["primary_reference"]["snapshot_path"]).relative_to(ROOT)
        ),
        "in_scope_levels": levels,
        "gates": {
            "reverse_coverage_pass": pass_gate,
            "min_coverage_pct": min_coverage_pct,
        },
        "counts": {
            "bunpro_in_scope_total": total,
            "covered_total": covered_total,
            "missing_taxonomy_total": len(missing_taxonomy),
            "missing_grammar_total": len(missing_grammar),
            "reverse_coverage_pct": coverage_pct,
            "by_level": by_level,
            "taxonomy_resolved_slugs": len(slug_index),
            "duplicate_taxonomy_mappings": sum(1 for v in slug_index.values() if len(v) > 1),
        },
        "details": {
            "missing_taxonomy_sample": missing_taxonomy[:100],
            "missing_grammar_sample": missing_grammar[:100],
            "duplicate_slug_mappings": {
                slug: pts for slug, pts in slug_index.items() if len(pts) > 1
            },
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    gates = report["gates"]
    counts = report["counts"]
    lines = [
        "# Bunpro Reverse Coverage Report",
        "",
        f"- Generated at: `{report['generated_at']}`",
        f"- Overall: **{'PASS' if gates['reverse_coverage_pass'] else 'FAIL'}** "
        f"(min `{gates['min_coverage_pct']}%`, actual `{counts['reverse_coverage_pct']}%`)",
        "",
        "## Counts",
        "",
        f"- Bunpro in-scope (JLPT5–1): `{counts['bunpro_in_scope_total']}`",
        f"- Covered (taxonomy + grammar cards): `{counts['covered_total']}`",
        f"- Missing taxonomy mapping: `{counts['missing_taxonomy_total']}`",
        f"- Taxonomy mapped but no grammar cards: `{counts['missing_grammar_total']}`",
        f"- Taxonomy slugs pointing at distinct Bunpro points: `{counts['taxonomy_resolved_slugs']}`",
        "",
        "## By JLPT level",
        "",
    ]
    for level, bucket in sorted(counts["by_level"].items()):
        lines.append(
            f"- `{level}`: covered `{bucket['covered']}/{bucket['total']}` "
            f"(missing taxonomy `{bucket['missing_taxonomy']}`, missing grammar `{bucket['missing_grammar']}`)"
        )
    lines.append("")
    missing = report["details"]["missing_taxonomy_sample"]
    if missing:
        lines.append("## Missing taxonomy (sample)")
        lines.append("")
        for row in missing[:40]:
            lines.append(
                f"- `{row['bunpro_slug']}` ({row['bunpro_level']}) {row.get('bunpro_title', '')}"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--min-coverage-pct",
        type=float,
        default=0.0,
        help="Fail if reverse_coverage_pct is below this threshold.",
    )
    parser.add_argument("--taxonomy", type=Path, default=None)
    parser.add_argument("--grammar-dir", type=Path, default=None)
    parser.add_argument("--report-json", type=Path, default=None)
    parser.add_argument("--report-md", type=Path, default=None)
    args = parser.parse_args()

    configure_paths(
        taxonomy=(ROOT / args.taxonomy) if args.taxonomy else None,
        grammar_dir=(ROOT / args.grammar_dir) if args.grammar_dir else None,
        report_json=(ROOT / args.report_json) if args.report_json else None,
        report_md=(ROOT / args.report_md) if args.report_md else None,
    )

    report = build_report(min_coverage_pct=args.min_coverage_pct)
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT_MD.write_text(render_markdown(report), encoding="utf-8")

    counts = report["counts"]
    gates = report["gates"]
    print(
        "bunpro_reverse_coverage: "
        f"overall={'PASS' if gates['reverse_coverage_pass'] else 'FAIL'} "
        f"pct={counts['reverse_coverage_pct']}% "
        f"covered={counts['covered_total']}/{counts['bunpro_in_scope_total']}"
    )
    print(f"report_json={REPORT_JSON}")
    print(f"report_md={REPORT_MD}")
    return 0 if gates["reverse_coverage_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
