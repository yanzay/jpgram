#!/usr/bin/env python3
"""
Generate prioritized pitch-accent override candidates with corpus examples.

Output:
  research-reports/pitchaccent_override_candidates.jsonl
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

WORDS_PATH = Path("media/words_index.json")
INDEX_PATH = Path("media/pitchaccent_index.json")
GRAMMAR_DIR = Path("grammar")
OUT_PATH = Path("research-reports/pitchaccent_override_candidates.jsonl")


def load_words() -> dict[str, int]:
    if not WORDS_PATH.exists():
        return {}
    data = json.loads(WORDS_PATH.read_text(encoding="utf-8"))
    out = {}
    for k, v in data.get("tokens", {}).items():
        if isinstance(v, int):
            out[k] = v
    return out


def load_index_meta() -> tuple[set[str], list[str]]:
    if not INDEX_PATH.exists():
        return set(), []
    data = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    covered = set(data.get("entries", {}).keys())
    missing = data.get("missing", [])
    return covered, [m for m in missing if isinstance(m, str)]


def collect_examples(tokens: set[str], max_examples: int = 3) -> dict[str, list[str]]:
    examples: dict[str, list[str]] = defaultdict(list)
    if not GRAMMAR_DIR.exists():
        return examples
    for tsv in sorted(GRAMMAR_DIR.rglob("*.tsv")):
        with tsv.open(encoding="utf-8") as fh:
            for raw in fh:
                line = raw.rstrip("\n")
                if not line or line.startswith("#"):
                    continue
                row = next(csv.reader([line], delimiter="\t", quotechar='"'))
                if not row:
                    continue
                jp = row[0]
                for token in tokens:
                    if token in jp and len(examples[token]) < max_examples:
                        ex = f"{tsv.parent.name}/{tsv.name}: {jp}"
                        if ex not in examples[token]:
                            examples[token].append(ex)
    return examples


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate pitch-accent override candidates")
    ap.add_argument("--top", type=int, default=300, help="max candidates to emit")
    args = ap.parse_args()

    words = load_words()
    covered, missing_queue = load_index_meta()
    if not words:
        print("No words index found; run build_furigana.py first.")
        return 1

    # Prioritize high-frequency uncovered tokens.
    candidates = [(t, words.get(t, 0)) for t in words.keys() if t not in covered]
    candidates.sort(key=lambda x: x[1], reverse=True)
    top = candidates[: args.top]
    token_set = {t for t, _ in top}
    ex = collect_examples(token_set)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as fh:
        for token, count in top:
            rec = {
                "token": token,
                "count": count,
                "in_missing_queue": token in missing_queue,
                "examples": ex.get(token, []),
                "proposed_override": {"reading": "", "accent": ""},
            }
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"✓ Wrote {len(top)} candidates -> {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
