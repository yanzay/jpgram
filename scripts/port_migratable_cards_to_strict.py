#!/usr/bin/env python3
"""
Port legacy card rows into grammar-strict/ when point tags map cleanly.

Only ports rows whose point:* tags are:
  - exempt rows present in strict taxonomy (same slug), or
  - legacy taxonomy resolved to a bunpro slug that is the strict point_slug

Skips bucket/auto-tagged rows (reported in bunpro_migration_report).
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
from grammar_reference import (  # noqa: E402
    ROOT,
    TAXONOMY_PATH,
    filename_safe_slug,
    load_taxonomy_rows,
    parse_bunpro_id,
    strict_deck_paths,
)

LEGACY_GRAMMAR = ROOT / "grammar"
MIGRATION_REPORT = ROOT / "research-reports/bunpro_migration_report.json"

MODULE_LABEL = {
    "00-foundation": "00 - Foundation",
    "01-n5": "01 - N5 Grammar",
    "02-n4": "02 - N4 Grammar",
    "03-n3": "03 - N3 Grammar",
    "04-n2": "04 - N2 Grammar",
    "05-n1": "05 - N1 Grammar",
    "06-keigo": "06 - Keigo",
    "07-casual": "07 - Casual",
    "08-slang": "08 - Slang",
    "09-sfp-aizuchi": "09 - SFP",
    "10-onomatopoeia": "10 - Onomatopoeia",
    "11-classical": "11 - Classical",
    "12-beyond-n1": "12 - Beyond N1",
    "13-l1": "13 - L1 Interference",
}


def build_point_map() -> dict[str, str]:
    legacy = {r["point_slug"]: r for r in load_taxonomy_rows(TAXONOMY_PATH)}
    strict_taxonomy, _, _ = strict_deck_paths()
    strict = {r["point_slug"]: r for r in load_taxonomy_rows(strict_taxonomy)}
    strict_slugs = set(strict)

    mapping: dict[str, str] = {}
    for slug in strict_slugs:
        mapping[slug] = slug
    for slug, row in legacy.items():
        status, bp = parse_bunpro_id(row["bunpro_id"])
        if status == "resolved" and bp in strict_slugs:
            mapping[slug] = bp
        elif status == "exempt" and slug in strict_slugs:
            mapping[slug] = slug
    return mapping


def retag_line(tags: str, point_map: dict[str, str], module: str, jlpt: str) -> str | None:
    parts = tags.split()
    new_parts: list[str] = []
    for part in parts:
        if part.startswith("point:"):
            old = part[len("point:") :]
            if old not in point_map:
                return None
            new_parts.append(f"point:{point_map[old]}")
        elif part.startswith("module:"):
            new_parts.append(f"module:{module}")
        elif part.startswith("jlpt:") and jlpt:
            new_parts.append(f"jlpt:{jlpt}")
        else:
            new_parts.append(part)
    return " ".join(new_parts)


def deck_name(module: str, note_type: str) -> str:
    label = MODULE_LABEL.get(module, module)
    return f"Japanese Grammar (Strict)::{label}::{note_type}"


def main() -> int:
    strict_taxonomy, strict_grammar, _ = strict_deck_paths()
    if not strict_taxonomy.exists():
        raise SystemExit(f"missing {strict_taxonomy}; run bootstrap_taxonomy_from_bunpro.py")

    strict_rows = {r["point_slug"]: r for r in load_taxonomy_rows(strict_taxonomy)}
    point_map = build_point_map()

    # dest_key = (module, point_slug, note_type) -> lines
    buckets: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    headers: dict[tuple[str, str, str], list[str]] = {}

    ported_rows = 0
    skipped_rows = 0

    for path in sorted(LEGACY_GRAMMAR.rglob("*.tsv")):
        note_type = ""
        module_hint = ""
        header_block: list[str] = []
        for raw in path.read_text(encoding="utf-8").splitlines():
            if raw.startswith("#notetype:"):
                note_type = raw.split(":", 1)[1].strip()
            if raw.startswith("#deck:"):
                header_block.append(raw)
            if raw.startswith("#") or not raw.strip():
                if raw.startswith("#"):
                    header_block.append(raw)
                continue
            row = next(csv.reader([raw], delimiter="\t", quotechar='"'))
            if not row:
                continue
            tags = row[-1]
            mapped = []
            for tag in tags.split():
                if tag.startswith("point:"):
                    old = tag[len("point:") :]
                    if old not in point_map:
                        mapped = []
                        break
                    mapped.append(point_map[old])
            if not mapped or len(set(mapped)) != 1:
                skipped_rows += 1
                continue
            target_point = mapped[0]
            meta = strict_rows[target_point]
            module = meta["module"]
            jlpt = meta["jlpt"]
            new_tags = retag_line(tags, point_map, module, jlpt)
            if not new_tags:
                skipped_rows += 1
                continue
            row[-1] = new_tags
            key = (module, target_point, note_type or "Unknown")
            if key not in headers:
                hb = [ln for ln in header_block if not ln.startswith("#deck:")]
                hb.append(f"#deck:{deck_name(module, note_type or 'Unknown')}")
                headers[key] = hb
            buckets[key].append("\t".join(row))
            ported_rows += 1

    strict_grammar.mkdir(parents=True, exist_ok=True)
    files_written = 0
    for (module, point_slug, note_type), body_lines in buckets.items():
        mod_dir = strict_grammar / module
        mod_dir.mkdir(parents=True, exist_ok=True)
        fname = f"{filename_safe_slug(point_slug)}_{note_type.lower()}.tsv"
        out_path = mod_dir / fname
        header = headers.get((module, point_slug, note_type), [])
        if not header:
            header = [
                "#separator:tab",
                "#html:true",
                f"#deck:{deck_name(module, note_type)}",
            ]
        content = "\n".join(header + [""] + body_lines) + "\n"
        out_path.write_text(content, encoding="utf-8")
        files_written += 1

    print(f"ported_rows={ported_rows} skipped_rows={skipped_rows}")
    print(f"files_written={files_written} grammar_dir={strict_grammar}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
