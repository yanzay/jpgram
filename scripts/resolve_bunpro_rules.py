#!/usr/bin/env python3
"""
Resolve high-confidence bunpro:auto mappings using deterministic rules.

Only applies mappings when:
- point slug belongs to a known family (demonstratives/copula/conditional/irregular verbs)
- mapped Bunpro slug exists in the live Bunpro snapshot
"""
from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
TAXONOMY_PATH = ROOT / "data/grammar_taxonomy.tsv"
BUNPRO_LIVE_PATH = ROOT / "data/grammar-refs/bunpro_live_index.json"


DEMO_MAP = {
    "kore": "これ",
    "sore": "それ",
    "are": "あれ",
    "dore": "どれ",
    "koko": "ここ",
    "soko": "そこ",
    "asoko": "あそこ",
    "doko": "どこ",
    "kono": "この",
    "sono": "その",
    "ano": "あの",
    "dono": "どの",
    "kou": "こう",
    "sou": "そう",
    "aa": "ああ",
    "dou": "どう",
    "konna": "こんな",
    "sonna": "そんな",
    "anna": "あんな",
    "donna": "どんな",
    "rule-ko": "これ",
    "rule-so": "それ",
    "rule-a": "あれ",
    "rule-do": "どれ",
}

COPULA_MAP = {
    "da": "だ",
    "desu": "です",
    "janai": "じゃない",
    "janakatta": "じゃなかった",
    "nara": "なら",
    "nari": "なり",
    "te": "で",
    "degozaimasu": "でございます",
}

CONDITIONAL_MAP = {
    "ba": "ば",
    "nara": "なら",
    "tara": "たら",
    "to": "と",
}

IRREGULAR_MAP = {
    "suru": "する",
    "kuru": "くる",
}


def map_point_to_bunpro_slug(point_slug: str) -> str | None:
    if point_slug.startswith("demonstrative-"):
        key = point_slug.split("demonstrative-", 1)[1]
        return DEMO_MAP.get(key)
    if point_slug.startswith("copula-"):
        key = point_slug.split("copula-", 1)[1]
        return COPULA_MAP.get(key)
    if point_slug.startswith("conditional-"):
        key = point_slug.split("conditional-", 1)[1]
        return CONDITIONAL_MAP.get(key)
    if point_slug.startswith("verb-irregular-"):
        key = point_slug.split("verb-irregular-", 1)[1]
        return IRREGULAR_MAP.get(key)
    return None


def main() -> int:
    if not TAXONOMY_PATH.exists():
        raise SystemExit(f"missing taxonomy: {TAXONOMY_PATH}")
    if not BUNPRO_LIVE_PATH.exists():
        raise SystemExit(f"missing Bunpro snapshot: {BUNPRO_LIVE_PATH}")

    bunpro = json.loads(BUNPRO_LIVE_PATH.read_text(encoding="utf-8"))
    bunpro_slugs = {p["slug"] for p in bunpro.get("points", [])}

    out_lines: list[str] = []
    changed = 0
    attempted = 0
    for raw in TAXONOMY_PATH.read_text(encoding="utf-8").splitlines():
        if not raw or raw.startswith("#"):
            out_lines.append(raw)
            continue
        row = next(csv.reader([raw], delimiter="\t", quotechar='"'))
        while len(row) < 9:
            row.append("")
        point_slug = row[0].strip()
        bunpro_id = row[3].strip()
        if not bunpro_id.startswith("bunpro:auto/"):
            out_lines.append("\t".join(row))
            continue

        mapped = map_point_to_bunpro_slug(point_slug)
        if mapped:
            attempted += 1
            if mapped in bunpro_slugs:
                row[3] = f"bunpro:{mapped}"
                changed += 1

        out_lines.append("\t".join(row))

    TAXONOMY_PATH.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    print(f"attempted_rule_mappings={attempted}")
    print(f"resolved_rule_mappings={changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
