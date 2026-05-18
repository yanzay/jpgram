#!/usr/bin/env python3
"""
Objective grammar coverage + example-density audit.

This script is intentionally strict and reproducible:
1) Audits internal closure (grammar TSV point tags vs taxonomy rows).
2) Fetches Bunpro live grammar index from bunpro.jp and snapshots it locally.
3) Verifies whether taxonomy Bunpro mappings are resolved (non-auto) and valid.
4) Audits per-point example density and note-type spread.

Outputs:
  - research-reports/coverage_audit_report.json
  - research-reports/coverage_audit_report.md
  - data/grammar-refs/bunpro_live_index.json (when fetch succeeds)
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
from grammar_reference import parse_bunpro_id  # noqa: E402


ROOT = Path(__file__).resolve().parent.parent
GRAMMAR_DIR = ROOT / "grammar-strict"
TAXONOMY_PATH = ROOT / "data/grammar_taxonomy_bunpro.tsv"
BUNPRO_LIVE_PATH = ROOT / "data/grammar-refs/bunpro_live_index.json"
REPORT_JSON_PATH = ROOT / "research-reports/coverage_audit_report.json"
REPORT_MD_PATH = ROOT / "research-reports/coverage_audit_report.md"


def configure_paths(
    *,
    taxonomy: Path | None = None,
    grammar_dir: Path | None = None,
    report_json: Path | None = None,
    report_md: Path | None = None,
) -> None:
    global GRAMMAR_DIR, TAXONOMY_PATH, REPORT_JSON_PATH, REPORT_MD_PATH
    if taxonomy is not None:
        TAXONOMY_PATH = taxonomy
    if grammar_dir is not None:
        GRAMMAR_DIR = grammar_dir
    if report_json is not None:
        REPORT_JSON_PATH = report_json
    if report_md is not None:
        REPORT_MD_PATH = report_md

SOURCE_BUNPRO_URL = "https://bunpro.jp/grammar_points"

NEXT_DATA_RE = re.compile(
    r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', re.S
)
JP_CHAR_RE = re.compile(r"[一-龯ぁ-んァ-ン]")
CLOZE_EXTRACT_RE = re.compile(r"\{\{c\d+::([^:}]+)(?:::[^}]+)?\}\}")


@dataclass
class PointUsage:
    rows: int = 0
    unique_sentences: set[str] | None = None
    note_types: set[str] | None = None
    modules: set[str] | None = None

    def __post_init__(self) -> None:
        self.unique_sentences = set()
        self.note_types = set()
        self.modules = set()


def fetch_text(url: str, timeout_s: int = 30) -> str:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 jpgram-coverage-audit"})
    with urlopen(req, timeout=timeout_s) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_bunpro_live(html: str) -> list[dict[str, Any]]:
    match = NEXT_DATA_RE.search(html)
    if not match:
        raise RuntimeError("Bunpro __NEXT_DATA__ payload not found")
    payload = json.loads(match.group(1))
    points = payload["props"]["pageProps"]["grammarPoints"]
    out: list[dict[str, Any]] = []
    for p in points:
        slug = str(p.get("slug", "")).strip()
        if not slug:
            continue
        out.append(
            {
                "id": p.get("id"),
                "slug": slug,
                "title": p.get("title"),
                "meaning": p.get("meaning"),
                "level": p.get("level"),
                "url": f"https://bunpro.jp/grammar_points/{slug}",
            }
        )
    return out


def snapshot_bunpro_live(html: str, points: list[dict[str, Any]]) -> None:
    BUNPRO_LIVE_PATH.parent.mkdir(parents=True, exist_ok=True)
    BUNPRO_LIVE_PATH.write_text(
        json.dumps(
            {
                "source": SOURCE_BUNPRO_URL,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "html_sha256": hashlib.sha256(html.encode("utf-8")).hexdigest(),
                "points_total": len(points),
                "points": points,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def load_taxonomy() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for raw in TAXONOMY_PATH.read_text(encoding="utf-8").splitlines():
        if not raw or raw.startswith("#"):
            continue
        row = next(csv.reader([raw], delimiter="\t", quotechar='"'))
        rows.append(
            {
                "point_slug": row[0].strip() if len(row) > 0 else "",
                "jlpt": row[1].strip() if len(row) > 1 else "",
                "module": row[2].strip() if len(row) > 2 else "",
                "bunpro_id": row[3].strip() if len(row) > 3 else "",
                "tofugu_url": row[4].strip() if len(row) > 4 else "",
                "imabi_url": row[5].strip() if len(row) > 5 else "",
            }
        )
    return rows


def detect_note_type(path: Path) -> str:
    stem = path.stem
    for nt in (
        "recognition",
        "production",
        "cloze",
        "contrast",
        "listening",
        "dictation",
    ):
        if stem.endswith(f"_{nt}"):
            return nt
    return "unknown"


def extract_source_sentence(note_type: str, header: list[str], row: list[str]) -> str:
    if note_type == "production":
        sample = row[header.index("Sample")].strip() if "Sample" in header else ""
        target = row[header.index("Target")].strip() if "Target" in header else ""
        if sample and JP_CHAR_RE.search(sample):
            return sample
        return target or sample
    if note_type == "cloze":
        text = row[header.index("Text")].strip() if "Text" in header else row[0].strip()
        return CLOZE_EXTRACT_RE.sub(r"\1", text)
    if note_type == "contrast":
        jp = row[header.index("JP")].strip() if "JP" in header else row[0].strip()
        ans = row[header.index("Answer")].strip() if "Answer" in header else ""
        return jp.replace("___", ans) if jp and ans else jp
    if note_type == "listening":
        return (
            row[header.index("Transcript")].strip()
            if "Transcript" in header
            else row[0].strip()
        )
    if note_type == "dictation":
        return row[header.index("Answer")].strip() if "Answer" in header else row[0].strip()
    return row[0].strip()


def collect_usage() -> dict[str, PointUsage]:
    usage: dict[str, PointUsage] = defaultdict(PointUsage)
    for path in sorted(GRAMMAR_DIR.rglob("*.tsv")):
        try:
            rel = path.relative_to(ROOT)
        except ValueError:
            rel = path
        module = rel.parts[1] if len(rel.parts) > 1 else "unknown"
        note_type = detect_note_type(path)

        lines = path.read_text(encoding="utf-8").splitlines()
        header: list[str] | None = None
        for line in lines:
            if line.startswith("#columns:"):
                header = line[len("#columns:") :].split("\t")
                break
        if not header:
            continue

        for raw in lines:
            if not raw or raw.startswith("#"):
                continue
            row = next(csv.reader([raw], delimiter="\t", quotechar='"'))
            if len(row) != len(header):
                continue
            tags = row[-1].split()
            points = [t[len("point:") :] for t in tags if t.startswith("point:")]
            if not points:
                continue
            sent = extract_source_sentence(note_type, header, row).strip()
            for pt in points:
                item = usage[pt]
                item.rows += 1
                item.note_types.add(note_type)
                item.modules.add(module)
                if sent:
                    item.unique_sentences.add(sent)
    return usage


def build_report(
    taxonomy_rows: list[dict[str, str]],
    usage: dict[str, PointUsage],
    bunpro_live_points: list[dict[str, Any]],
    min_unique_sentences: int,
    min_note_types: int,
    min_unique_sentences_foundation: int,
    enforce_note_types: bool,
    require_full_bunpro_resolution: bool,
    allow_partial_point_usage: bool = False,
) -> dict[str, Any]:
    taxonomy_points = {r["point_slug"] for r in taxonomy_rows if r["point_slug"]}
    used_points = set(usage.keys())

    missing_in_grammar = sorted(taxonomy_points - used_points)
    extra_in_grammar = sorted(used_points - taxonomy_points)

    bunpro_live_slug_set = {p["slug"] for p in bunpro_live_points}
    bunpro_status = Counter()
    bunpro_match = Counter()
    bunpro_unmatched_rows: list[dict[str, str]] = []

    for row in taxonomy_rows:
        point_slug = row["point_slug"]
        status, mapped_slug = parse_bunpro_id(row["bunpro_id"])
        bunpro_status[status] += 1
        if status != "resolved":
            continue
        if mapped_slug in bunpro_live_slug_set:
            bunpro_match["matched"] += 1
        else:
            bunpro_match["unmatched"] += 1
            bunpro_unmatched_rows.append(
                {
                    "point_slug": point_slug,
                    "bunpro_id": row["bunpro_id"],
                    "normalized_bunpro_slug": mapped_slug,
                }
            )

    sparse_examples: list[dict[str, Any]] = []
    sparse_note_types: list[dict[str, Any]] = []
    for point in sorted(used_points):
        item = usage[point]
        unique_sentences = len(item.unique_sentences)
        note_types = sorted(item.note_types)
        modules = sorted(item.modules)
        min_examples = (
            min_unique_sentences_foundation if "00-foundation" in modules else min_unique_sentences
        )
        if unique_sentences < min_examples:
            sparse_examples.append(
                {
                    "point_slug": point,
                    "required_unique_sentences": min_examples,
                    "unique_sentences": unique_sentences,
                    "rows": item.rows,
                    "note_types": note_types,
                    "modules": modules,
                }
            )
        if len(note_types) < min_note_types:
            sparse_note_types.append(
                {
                    "point_slug": point,
                    "note_type_count": len(note_types),
                    "note_types": note_types,
                    "rows": item.rows,
                    "unique_sentences": unique_sentences,
                    "modules": modules,
                }
            )

    internal_closed_set_pass = not extra_in_grammar and (
        allow_partial_point_usage or not missing_in_grammar
    )
    mapping_debt = (
        bunpro_status["auto"]
        + bunpro_status["missing"]
        + bunpro_status["malformed"]
    )
    bunpro_mapping_resolved_pass = mapping_debt == 0
    # Valid means every explicitly-resolved mapping points to a live Bunpro slug.
    # Unresolved auto-mappings are tracked separately as mapping debt.
    bunpro_mapping_valid_pass = bunpro_match["unmatched"] == 0
    examples_density_pass = len(sparse_examples) == 0
    note_type_spread_pass = len(sparse_note_types) == 0

    taxonomy_total = len(taxonomy_rows)
    used_total = len(used_points)
    resolved_total = bunpro_status["resolved"]
    exempt_total = bunpro_status["exempt"]
    mapped_total = resolved_total + exempt_total
    matched_total = bunpro_match["matched"]
    sparse_examples_total = len(sparse_examples)
    sparse_note_types_total = len(sparse_note_types)

    internal_point_coverage_pct = (
        round((used_total / taxonomy_total) * 100, 2) if taxonomy_total else 0.0
    )
    bunpro_resolution_coverage_pct = (
        round((mapped_total / taxonomy_total) * 100, 2) if taxonomy_total else 0.0
    )
    bunpro_resolved_validity_pct = (
        round((matched_total / resolved_total) * 100, 2) if resolved_total else 0.0
    )
    examples_density_coverage_pct = (
        round(((used_total - sparse_examples_total) / used_total) * 100, 2) if used_total else 0.0
    )
    note_type_spread_coverage_pct = (
        round(((used_total - sparse_note_types_total) / used_total) * 100, 2) if used_total else 0.0
    )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "taxonomy_path": str(TAXONOMY_PATH.relative_to(ROOT)),
            "grammar_dir": str(GRAMMAR_DIR.relative_to(ROOT)),
            "bunpro_live_source": SOURCE_BUNPRO_URL,
        },
        "gates": {
            "internal_closed_set_pass": internal_closed_set_pass,
            "bunpro_mapping_resolved_pass": bunpro_mapping_resolved_pass,
            "bunpro_mapping_valid_pass": bunpro_mapping_valid_pass,
            "examples_density_pass": examples_density_pass,
            "note_type_spread_pass": note_type_spread_pass,
            "overall_pass": all(
                [
                    internal_closed_set_pass,
                    bunpro_mapping_valid_pass,
                    examples_density_pass,
                    note_type_spread_pass if enforce_note_types else True,
                    bunpro_mapping_resolved_pass if require_full_bunpro_resolution else True,
                ]
            ),
        },
        "counts": {
            "taxonomy_points_total": taxonomy_total,
            "used_points_total": used_total,
            "missing_taxonomy_points_in_grammar": len(missing_in_grammar),
            "extra_points_in_grammar_not_in_taxonomy": len(extra_in_grammar),
            "bunpro_live_points_total": len(bunpro_live_points),
            "bunpro_mapping_status": dict(bunpro_status),
            "bunpro_mapping_debt": mapping_debt,
            "bunpro_mapping_matches": dict(bunpro_match),
            "points_below_min_unique_sentences": sparse_examples_total,
            "points_below_min_note_types": sparse_note_types_total,
        },
        "coverage_percentages": {
            "internal_point_coverage_pct": internal_point_coverage_pct,
            "bunpro_resolution_coverage_pct": bunpro_resolution_coverage_pct,
            "bunpro_resolved_validity_pct": bunpro_resolved_validity_pct,
            "examples_density_coverage_pct": examples_density_coverage_pct,
            "note_type_spread_coverage_pct": note_type_spread_coverage_pct,
        },
        "thresholds": {
            "min_unique_sentences_per_point": min_unique_sentences,
            "min_unique_sentences_foundation": min_unique_sentences_foundation,
            "min_note_types_per_point": min_note_types,
            "enforce_note_types": enforce_note_types,
            "require_full_bunpro_resolution": require_full_bunpro_resolution,
            "allow_partial_point_usage": allow_partial_point_usage,
        },
        "details": {
            "missing_in_grammar": missing_in_grammar,
            "extra_in_grammar_not_in_taxonomy": extra_in_grammar,
            "bunpro_unmatched_resolved_rows": bunpro_unmatched_rows[:200],
            "sparse_examples": sparse_examples[:500],
            "sparse_note_types": sparse_note_types[:500],
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    gates = report["gates"]
    counts = report["counts"]
    coverage = report.get("coverage_percentages", {})
    thr = report["thresholds"]
    details = report["details"]

    def gate(v: bool) -> str:
        return "PASS" if v else "FAIL"

    lines: list[str] = []
    lines.append("# Coverage Audit Report")
    lines.append("")
    lines.append(f"- Generated at: `{report['generated_at']}`")
    lines.append(f"- Overall: **{gate(gates['overall_pass'])}**")
    lines.append("")
    lines.append("## Objective Gates")
    lines.append("")
    lines.append(f"- Internal closed set: **{gate(gates['internal_closed_set_pass'])}**")
    lines.append(f"- Bunpro mapping resolved: **{gate(gates['bunpro_mapping_resolved_pass'])}**")
    lines.append(f"- Bunpro mapping valid: **{gate(gates['bunpro_mapping_valid_pass'])}**")
    lines.append(f"- Example density: **{gate(gates['examples_density_pass'])}**")
    lines.append(f"- Note-type spread: **{gate(gates['note_type_spread_pass'])}**")
    lines.append("")
    lines.append("## Counts")
    lines.append("")
    lines.append(f"- Taxonomy points: `{counts['taxonomy_points_total']}`")
    lines.append(f"- Used points in grammar TSVs: `{counts['used_points_total']}`")
    lines.append(f"- Bunpro live points: `{counts['bunpro_live_points_total']}`")
    lines.append(
        f"- Bunpro mapping status: `{json.dumps(counts['bunpro_mapping_status'], ensure_ascii=False)}`"
    )
    lines.append(
        f"- Bunpro mapping matches: `{json.dumps(counts['bunpro_mapping_matches'], ensure_ascii=False)}`"
    )
    lines.append(
        f"- Points below `{thr['min_unique_sentences_per_point']}` unique sentences: "
        f"`{counts['points_below_min_unique_sentences']}`"
    )
    lines.append(
        f"- Foundation threshold (`00-foundation`): `{thr['min_unique_sentences_foundation']}` unique sentence(s)"
    )
    lines.append(
        f"- Points below `{thr['min_note_types_per_point']}` note types: "
        f"`{counts['points_below_min_note_types']}`"
    )
    lines.append("")
    lines.append("## Coverage Percentages")
    lines.append("")
    lines.append(
        f"- Internal point coverage: `{coverage.get('internal_point_coverage_pct', 0.0)}%`"
    )
    lines.append(
        f"- Bunpro mapping closure (resolved+exempt): "
        f"`{coverage.get('bunpro_resolution_coverage_pct', 0.0)}%`"
    )
    lines.append(
        f"- Bunpro mapping debt (auto/missing/malformed): "
        f"`{counts.get('bunpro_mapping_debt', 0)}`"
    )
    lines.append(
        f"- Bunpro resolved validity: `{coverage.get('bunpro_resolved_validity_pct', 0.0)}%`"
    )
    lines.append(
        f"- Example-density coverage: `{coverage.get('examples_density_coverage_pct', 0.0)}%`"
    )
    lines.append(
        f"- Note-type spread coverage: `{coverage.get('note_type_spread_coverage_pct', 0.0)}%`"
    )
    lines.append("")

    if details["missing_in_grammar"]:
        lines.append("## Missing In Grammar")
        lines.append("")
        for p in details["missing_in_grammar"][:50]:
            lines.append(f"- `{p}`")
        lines.append("")

    if details["sparse_examples"]:
        lines.append("## Sparse Examples (sample)")
        lines.append("")
        for row in details["sparse_examples"][:50]:
            lines.append(
                f"- `{row['point_slug']}`: sentences={row['unique_sentences']} rows={row['rows']} "
                f"notes={','.join(row['note_types'])}"
            )
        lines.append("")

    if details["sparse_note_types"]:
        lines.append("## Sparse Note Types (sample)")
        lines.append("")
        for row in details["sparse_note_types"][:50]:
            lines.append(
                f"- `{row['point_slug']}`: note_types={row['note_type_count']} "
                f"({','.join(row['note_types'])}) sentences={row['unique_sentences']}"
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--min-unique-sentences",
        type=int,
        default=5,
        help="Minimum unique source sentences required per non-foundation point.",
    )
    parser.add_argument(
        "--min-unique-sentences-foundation",
        type=int,
        default=1,
        help="Minimum unique source sentences required per 00-foundation point.",
    )
    parser.add_argument(
        "--min-note-types",
        type=int,
        default=2,
        help="Minimum note-type spread required per point.",
    )
    parser.add_argument(
        "--enforce-note-types",
        action="store_true",
        help="If set, note-type spread failures affect overall PASS/FAIL.",
    )
    parser.add_argument(
        "--require-full-bunpro-resolution",
        action="store_true",
        help="If set, unresolved bunpro:auto rows fail the overall gate.",
    )
    parser.add_argument(
        "--skip-bunpro-fetch",
        action="store_true",
        help="Do not fetch Bunpro live page. Reuse local bunpro_live_index.json.",
    )
    parser.add_argument(
        "--taxonomy",
        type=Path,
        default=None,
        help="Taxonomy TSV path (default: data/grammar_taxonomy.tsv).",
    )
    parser.add_argument(
        "--grammar-dir",
        type=Path,
        default=None,
        help="Grammar TSV root (default: grammar/).",
    )
    parser.add_argument(
        "--report-json",
        type=Path,
        default=None,
        help="Output JSON report path.",
    )
    parser.add_argument(
        "--report-md",
        type=Path,
        default=None,
        help="Output Markdown report path.",
    )
    parser.add_argument(
        "--allow-partial-point-usage",
        action="store_true",
        help="Pass internal closure when grammar tags are valid, even if many taxonomy rows lack cards yet.",
    )
    args = parser.parse_args()

    configure_paths(
        taxonomy=(ROOT / args.taxonomy) if args.taxonomy else None,
        grammar_dir=(ROOT / args.grammar_dir) if args.grammar_dir else None,
        report_json=(ROOT / args.report_json) if args.report_json else None,
        report_md=(ROOT / args.report_md) if args.report_md else None,
    )

    if not TAXONOMY_PATH.exists():
        print(f"Missing taxonomy file: {TAXONOMY_PATH}", file=sys.stderr)
        return 1

    bunpro_live_points: list[dict[str, Any]]
    if args.skip_bunpro_fetch and BUNPRO_LIVE_PATH.exists():
        bunpro_live_points = json.loads(BUNPRO_LIVE_PATH.read_text(encoding="utf-8"))["points"]
    else:
        try:
            html = fetch_text(SOURCE_BUNPRO_URL)
            bunpro_live_points = parse_bunpro_live(html)
            snapshot_bunpro_live(html, bunpro_live_points)
        except (URLError, RuntimeError, KeyError, json.JSONDecodeError) as err:
            print(f"Bunpro fetch/parse failed: {err}", file=sys.stderr)
            if BUNPRO_LIVE_PATH.exists():
                bunpro_live_points = json.loads(BUNPRO_LIVE_PATH.read_text(encoding="utf-8"))[
                    "points"
                ]
            else:
                return 1

    taxonomy_rows = load_taxonomy()
    usage = collect_usage()
    report = build_report(
        taxonomy_rows=taxonomy_rows,
        usage=usage,
        bunpro_live_points=bunpro_live_points,
        min_unique_sentences=args.min_unique_sentences,
        min_note_types=args.min_note_types,
        min_unique_sentences_foundation=args.min_unique_sentences_foundation,
        enforce_note_types=args.enforce_note_types,
        require_full_bunpro_resolution=args.require_full_bunpro_resolution,
        allow_partial_point_usage=args.allow_partial_point_usage,
    )

    REPORT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    REPORT_MD_PATH.write_text(render_markdown(report), encoding="utf-8")

    gates = report["gates"]
    print(
        "coverage_audit: "
        f"overall={'PASS' if gates['overall_pass'] else 'FAIL'} "
        f"(internal={gates['internal_closed_set_pass']}, "
        f"bunpro_resolved={gates['bunpro_mapping_resolved_pass']}, "
        f"bunpro_valid={gates['bunpro_mapping_valid_pass']}, "
        f"examples={gates['examples_density_pass']}, "
        f"note_types={gates['note_type_spread_pass']})"
    )
    print(f"report_json={REPORT_JSON_PATH}")
    print(f"report_md={REPORT_MD_PATH}")
    print(f"bunpro_live_snapshot={BUNPRO_LIVE_PATH}")

    return 0 if gates["overall_pass"] else 2


if __name__ == "__main__":
    sys.exit(main())
