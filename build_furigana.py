#!/usr/bin/env python3
"""
Tier-2 furigana builder for the Japanese Grammar Anki package.

Generates a per-sentence reading index so Anki cards can show:
  • original sentence with kanji
  • ruby-annotated form with hiragana over each kanji run
  • plain hiragana reading
  • Hepburn romaji

Backend: pykakasi + fugashi/unidic-lite (MeCab).
Output:
  media/furigana_index.json   — sha1[:12] → {plain, ruby, hira, romaji}
  media/words_index.json      — vocab token frequency across the corpus

Idempotent: only re-processes sentences whose hash isn't already in the
index (run with --force to rebuild).

This is the JP analog of the English IPA builder. Furigana exists because
Japanese orthography is non-phonemic on the kanji side: the SAME kanji
can have wildly different readings depending on grammar context (生きる
ikiru vs 生まれる umareru vs 先生 sensei vs 一生 isshou). Showing a
machine-generated reading on the back of a card is the JP equivalent of
showing IPA on an English card.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Dict, List

INDEX_PATH = Path("media/furigana_index.json")
WORDS_PATH = Path("media/words_index.json")
GRAMMAR_DIR = Path("grammar")

INDEX_VERSION = 1

_CLOZE_RE = re.compile(r"\{\{c\d+::([^:}]+)(?:::[^}]+)?\}\}")


def text_hash(text: str) -> str:
    return hashlib.sha1(text.strip().encode("utf-8")).hexdigest()[:12]


# ── Tokenizer / converter (lazy) ─────────────────────────────────────────
_TAGGER = None
_KKS = None


def _tagger():
    global _TAGGER
    if _TAGGER is None:
        try:
            import fugashi  # type: ignore
        except ImportError as e:
            raise SystemExit(
                "Furigana builder needs `fugashi` + `unidic-lite`.\n"
                "  pip install fugashi unidic-lite"
            ) from e
        _TAGGER = fugashi.Tagger()
    return _TAGGER


def _kakasi():
    global _KKS
    if _KKS is None:
        try:
            import pykakasi  # type: ignore
        except ImportError as e:
            raise SystemExit(
                "Furigana builder needs `pykakasi`.\n"
                "  pip install pykakasi"
            ) from e
        _KKS = pykakasi.kakasi()
    return _KKS


# ── Conversion ───────────────────────────────────────────────────────────
def annotate(text: str) -> dict:
    """Return {plain, ruby, hira, romaji} for one sentence."""
    kks = _kakasi()
    converted = kks.convert(text)
    hira = "".join(c.get("hira", "") for c in converted)
    romaji = " ".join(c.get("hepburn", "") for c in converted if c.get("hepburn"))

    # Build an HTML <ruby> form: only annotate runs that contain kanji.
    parts: List[str] = []
    for c in converted:
        orig = c.get("orig", "")
        h = c.get("hira", "")
        if any("\u4e00" <= ch <= "\u9fff" for ch in orig) and h and h != orig:
            parts.append(f"<ruby>{orig}<rt>{h}</rt></ruby>")
        else:
            parts.append(orig)
    ruby = "".join(parts)

    return {"plain": text, "ruby": ruby, "hira": hira, "romaji": romaji}


# ── Corpus extraction ────────────────────────────────────────────────────
def collect_sentences() -> List[str]:
    sentences = set()
    if not GRAMMAR_DIR.exists():
        return []
    import csv
    for tsv in sorted(GRAMMAR_DIR.rglob("*.tsv")):
        is_cloze = "cloze" in tsv.parts or tsv.name.startswith("cloze_")
        for raw in tsv.read_text(encoding="utf-8").splitlines():
            if not raw or raw.startswith("#"):
                continue
            row = next(csv.reader([raw], delimiter="\t", quotechar='"'))
            if not row:
                continue
            jp = row[0].strip()
            if not jp:
                continue
            if is_cloze:
                jp = _CLOZE_RE.sub(r"\1", jp)
            sentences.add(jp)
    return sorted(sentences)


# ── Index I/O ────────────────────────────────────────────────────────────
def load_index() -> dict:
    if INDEX_PATH.exists():
        try:
            data = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
            if data.get("version") == INDEX_VERSION and "entries" in data:
                return data
        except json.JSONDecodeError:
            pass
    return {"version": INDEX_VERSION, "entries": {}}


def save_index(idx: dict) -> None:
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    idx["entries"] = dict(sorted(idx["entries"].items()))
    INDEX_PATH.write_text(
        json.dumps(idx, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main():
    ap = argparse.ArgumentParser(description="JP furigana / reading index builder")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--force", action="store_true",
                    help="Re-annotate every sentence (default: only new)")
    ap.add_argument("--no-words", action="store_true",
                    help="Skip the per-token vocabulary index")
    args = ap.parse_args()

    sentences = collect_sentences()
    if args.limit:
        sentences = sentences[:args.limit]

    idx = load_index()
    entries: Dict[str, dict] = idx["entries"]
    print(f"Corpus: {len(sentences)} unique JP sentences.")

    written = up_to_date = 0
    for i, text in enumerate(sentences, 1):
        h = text_hash(text)
        if not args.force and h in entries and entries[h].get("hira"):
            up_to_date += 1
        else:
            entries[h] = annotate(text)
            written += 1
        if i % 200 == 0 or i == len(sentences):
            print(f"  [{i}/{len(sentences)}] written={written} up-to-date={up_to_date}")

    save_index(idx)
    print(f"\n✓ Furigana index → {INDEX_PATH}")

    # ── Per-token vocabulary frequency ──
    if not args.no_words:
        from collections import Counter
        counter: Counter[str] = Counter()
        tagger = None
        try:
            tagger = _tagger()
        except SystemExit as e:
            print(f"  (fugashi unavailable, using regex tokenization: {e})", file=sys.stderr)
        for text in sentences:
            if tagger is not None:
                for tok in tagger(text):
                    surface = tok.surface
                    if surface.strip() and any(ch.isalpha() or "\u3040" <= ch <= "\u9fff" for ch in surface):
                        counter[surface] += 1
            else:
                for surface in re.findall(r"[一-龯ぁ-ゖァ-ヺー]+", text):
                    if surface.strip():
                        counter[surface] += 1
        WORDS_PATH.parent.mkdir(parents=True, exist_ok=True)
        WORDS_PATH.write_text(
            json.dumps({"version": 1,
                        "tokens": dict(counter.most_common())},
                       indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"✓ Words index   → {WORDS_PATH} ({len(counter)} unique tokens)")


if __name__ == "__main__":
    main()
