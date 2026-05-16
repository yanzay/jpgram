#!/usr/bin/env python3
"""
Tier-2 pitch-accent index builder.

Premium Japanese decks (NHK Pronunciation Dictionary, OJAD, Dogen) ship
**per-word pitch-accent annotations** so learners can hear *and* see the
accent pattern on every card. This script builds that index from
multiple authoritative sources, in priority order:

  1. Local Kanjium / wadoku-derived pitch-accent SQLite (if present
     at data/accents.sqlite — recommended by Yomitan community).
  2. Local NHK accent CSV dump (if present at data/nhk_accents.csv).
  3. Wadoku's open accent_db.tsv (if present at data/wadoku_accents.tsv).

Each token from media/words_index.json (built by build_furigana.py) is
looked up in turn; the highest-priority hit wins. Tokens with no match
are reported (so we can curate them by hand).

Output:
  media/pitchaccent_index.json  →
    { "version": 1,
      "entries": {
        "学生":   {"reading":"がくせい",   "accent":"0", "pattern":"LHHH"},
        "先生":   {"reading":"せんせい",   "accent":"3", "pattern":"LHHL"},
        "橋":     {"reading":"はし",       "accent":"2", "pattern":"LH"},
        "箸":     {"reading":"はし",       "accent":"1", "pattern":"HL"},
        ...
      },
      "missing":  ["…tokens with no source hit…"] }

The card layout (added in Wave 1) overlays the pattern as a colored
contour above the kanji, and as numeric Tokyo-style notation
(e.g. ◯⁰ heiban, ¹atamadaka, ²nakadaka, ³odaka, …) on the back.

This file is a SKELETON: it declares the lookup pipeline and output
schema; the source-data ingestion functions are implemented in Wave 2
once the data files are added under `data/` (.gitignored — bring your
own license-permitting source).
"""
from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
from pathlib import Path
from typing import Optional

WORDS_PATH = Path("media/words_index.json")
OUT_PATH = Path("media/pitchaccent_index.json")
DATA_DIR = Path("data")

INDEX_VERSION = 1


# ── Source loaders (skeleton; ingestion implemented in Wave 2) ───────────
def _kanjium(token: str) -> Optional[dict]:
    db = DATA_DIR / "accents.sqlite"
    if not db.exists():
        return None
    try:
        con = sqlite3.connect(db)
        cur = con.execute(
            "SELECT reading, accent FROM accents WHERE expression = ?",
            (token,),
        )
        row = cur.fetchone()
        con.close()
        if row:
            reading, accent = row
            return {"reading": reading, "accent": str(accent),
                    "pattern": _accent_to_pattern(reading, int(accent)),
                    "source": "kanjium"}
    except sqlite3.DatabaseError:
        pass
    return None


def _nhk(token: str) -> Optional[dict]:
    csv_path = DATA_DIR / "nhk_accents.csv"
    if not csv_path.exists():
        return None
    # Wave 2: cache the CSV in a module-level dict on first call.
    return None


def _wadoku(token: str) -> Optional[dict]:
    tsv_path = DATA_DIR / "wadoku_accents.tsv"
    if not tsv_path.exists():
        return None
    return None


SOURCES = [_kanjium, _nhk, _wadoku]


def _accent_to_pattern(reading: str, accent: int) -> str:
    """Convert Tokyo accent number → coarse L/H mora-by-mora pattern.

      accent = 0 → heiban   (LHHH…)
      accent = 1 → atamadaka(HLLL…)
      accent = N → nakadaka, drop after the N-th mora.

    Counts "mora" as kana characters minus standalone yō-on (ゃゅょ),
    which attach to the previous mora. Long vowels and っ each count
    as one mora.
    """
    moras = []
    for ch in reading:
        if ch in "ゃゅょャュョ" and moras:
            moras[-1] += ch
        else:
            moras.append(ch)
    n = len(moras)
    if n == 0:
        return ""
    if accent == 0:
        return "L" + "H" * (n - 1)
    if accent == 1:
        return "H" + "L" * (n - 1)
    return "L" + "H" * (accent - 1) + "L" * (n - accent)


def lookup(token: str) -> Optional[dict]:
    for src in SOURCES:
        hit = src(token)
        if hit:
            return hit
    return None


# ── Driver ───────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser(description="Build per-token pitch-accent index")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--report-missing", action="store_true",
                    help="Print every token with no source hit")
    args = ap.parse_args()

    if not WORDS_PATH.exists():
        print(f"{WORDS_PATH} not found — run build_furigana.py first.")
        return 1

    words = json.loads(WORDS_PATH.read_text(encoding="utf-8")).get("tokens", {})
    tokens = list(words.keys())
    if args.limit:
        tokens = tokens[:args.limit]

    entries: dict[str, dict] = {}
    missing: list[str] = []
    for t in tokens:
        hit = lookup(t)
        if hit:
            entries[t] = hit
        else:
            missing.append(t)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(
        json.dumps({"version": INDEX_VERSION,
                    "entries": entries,
                    "missing_count": len(missing),
                    "missing": missing[:200] if args.report_missing else []},
                   indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"✓ Pitch-accent index → {OUT_PATH} "
          f"({len(entries)}/{len(tokens)} tokens, "
          f"{len(missing)} missing)")
    if not entries:
        print("  (no source data under data/ — see header docstring)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
