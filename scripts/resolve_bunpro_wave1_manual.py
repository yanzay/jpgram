#!/usr/bin/env python3
"""
Wave 1: apply manually curated high-confidence Bunpro mappings.

Scope:
- Only updates rows still on bunpro:auto/*
- Only applies mappings that exist in live Bunpro snapshot
- Intended to increase real external coverage safely
"""
from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
TAXONOMY_PATH = ROOT / "data/grammar_taxonomy.tsv"
BUNPRO_LIVE_PATH = ROOT / "data/grammar-refs/bunpro_live_index.json"


# point_slug -> bunpro slug (must exist in Bunpro live snapshot)
WAVE1_MAP = {
    "advice-experience": "ことがある",
    "conditional": "たら",
    "tokoro": "たところだ",
    "tokoro-aspectual": "るところだ",
    "evidentials-sou": "そうだ",
    "evidentials-other": "みたい",
    "evidentials": "っぽい",
    "giving-receiving": "あげる",
    "benefactive": "あげる",
    "koto-nominalisations": "ことがある",
    "concessive-noni": "のに",
    "embedded-questions": "かどうか",
    "relative-nouns": "とおり",
    "n3-keigo-trans": "ございます",
    "formal-condition-restriction": "限り",
    "formal-explicative": "ということだ",
    "formal-modality-have-to": "ないわけにはいかない",
    "formal-modality-judgement": "はずだ",
    "passive-discourse": "とは",
    "n1-discourse-markers": "そういえば",
    "n1-modality-judgement-advanced": "に相違ない",
    "n1-emphasis": "の極み",
    "n1-limit-only": "のなんのって",
    "n1-stiff-rare": "が早いか",
    "n1-restriction": "に足る",
    "literary-temporal": "や否や",
    "customer-service-phrases": "いたす",
    "business-set-phrases": "いたす",
    "kenjogo-verbs": "いたす",
    "phone-keigo": "いたす",
    "o-stem-ni-naru-suru": "いたす",
    "sonkeigo-verbs": "いらっしゃる",
    "te-aux-family": "ていく",
}

# Wave 1.1: high-evidence candidates (evidence >= 14), verified in live Bunpro snapshot
WAVE1_1_MAP = {
    "temporal-na-uchini": "うちに",
    "temporal-formal": "ながら",
    "listing-formal": "だの",
    "formal-causal": "からこそ",
    "extent-degree": "ほど",
    "iru-eru-stiff": "ないではいられない",
    "bakari-dake-shika": "ばかり",
    "koto-mono": "ものだ",
    "n2-misc-discourse": "とは",
    "formal-result": "あげく",
    "formal-conjunctions": "および",
    "bakari-extensions": "ばかり",
    "wake-family": "わけだ",
    "formal-causal-contrast": "あげく",
    "formal-modality": "ものか",
    "attendant-stiff": "につれて",
    "formal-attendant-stiff-cloze": "につれて",
    "conditional-formal": "であれ",
    "formal-modality-attempt": "ものか",
    "causal-result": "せいで",
    "tokoro-n3": "ところが",
    "formal-stiff-contrast": "ないではいられない",
    "concessive": "ながらも",
    "n3-misc": "だらけ",
    "extremity-emphasis": "どころか",
    "formal-attendant": "にしたがって",
    "formal-stiff": "わけにはいかない",
    "n1-modality": "にすぎない",
    "listing-extremity": "どころか",
    "taru-gotoki": "たる",
}

CURATED_MAP = {**WAVE1_MAP, **WAVE1_1_MAP}


def main() -> int:
    if not TAXONOMY_PATH.exists():
        raise SystemExit(f"missing taxonomy: {TAXONOMY_PATH}")
    if not BUNPRO_LIVE_PATH.exists():
        raise SystemExit(f"missing Bunpro snapshot: {BUNPRO_LIVE_PATH}")

    bunpro = json.loads(BUNPRO_LIVE_PATH.read_text(encoding="utf-8"))
    bunpro_slugs = {p["slug"] for p in bunpro.get("points", [])}

    out_lines: list[str] = []
    attempted = 0
    applied = 0
    skipped_missing_slug = []

    for raw in TAXONOMY_PATH.read_text(encoding="utf-8").splitlines():
        if not raw or raw.startswith("#"):
            out_lines.append(raw)
            continue
        row = next(csv.reader([raw], delimiter="\t", quotechar='"'))
        while len(row) < 9:
            row.append("")
        point_slug = row[0].strip()
        bunpro_id = row[3].strip()

        mapped = CURATED_MAP.get(point_slug)
        if mapped and bunpro_id.startswith("bunpro:auto/"):
            attempted += 1
            if mapped in bunpro_slugs:
                row[3] = f"bunpro:{mapped}"
                applied += 1
            else:
                skipped_missing_slug.append((point_slug, mapped))

        out_lines.append("\t".join(row))

    TAXONOMY_PATH.write_text("\n".join(out_lines) + "\n", encoding="utf-8")

    print(f"attempted_curated={attempted}")
    print(f"applied_curated={applied}")
    print(f"wave1_entries={len(WAVE1_MAP)} wave1_1_entries={len(WAVE1_1_MAP)}")
    if skipped_missing_slug:
        print("skipped_missing_bunpro_slug:")
        for p, m in skipped_missing_slug:
            print(f"  {p} -> {m}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
