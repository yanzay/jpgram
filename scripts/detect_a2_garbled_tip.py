#!/usr/bin/env python3
"""A2 — Garbled-Tip detector for *_contrast.tsv files.

Flags Tip cells that show signs of placeholder leak or
script-mixing concatenation errors. Heuristics:
  - Substring "(this form)" present (template placeholder leak).
  - Japanese kanji/kana directly concatenated with lowercase Latin word
    (no space between scripts) — e.g. "forcedを得ない".
  - Tip is empty / only whitespace / only punctuation.
  - Tip contains a stray " . " (space-period-space) mid-sentence.

Stdlib only.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "grammar-strict"

JP_RE = re.compile(r"[぀-ゟ゠-ヿ一-鿿]")
LATIN_LOWER = "[a-z]"
JP_CHARS = r"[぀-ゟ゠-ヿ一-鿿]"
# latin word touching JP char with no whitespace/punct between
SCRIPT_GLUE = re.compile(rf"{LATIN_LOWER}{JP_CHARS}|{JP_CHARS}{LATIN_LOWER}")

PUNCT_ONLY = re.compile(r"^[\s\W_]+$", re.UNICODE)
STRAY_PERIOD = re.compile(r"[a-zA-Z]\s\.\s[a-zA-Z]")


def reasons(tip: str) -> list[str]:
    out: list[str] = []
    if "(this form)" in tip:
        out.append("placeholder-leak:(this form)")
    if SCRIPT_GLUE.search(tip):
        # but allow cases where the latin word is a single-letter abbrev like
        # "V" or "N" used in formula shorthand: V-て, N-が — these are normal.
        # Filter: glue letter must be lowercase a-z AND preceded/followed by
        # multiple Latin letters (i.e., a real English word).
        m = re.search(rf"([a-z]{{2,}}){JP_CHARS}", tip)
        m2 = re.search(rf"{JP_CHARS}([a-z]{{2,}})", tip)
        if m or m2:
            out.append("script-glue:latin↔JP")
    if not tip or not tip.strip():
        out.append("empty")
    elif PUNCT_ONLY.match(tip):
        out.append("punct-only")
    if STRAY_PERIOD.search(tip):
        out.append("stray-period")
    return out


def detect(root: Path) -> list[dict]:
    hits: list[dict] = []
    for path in sorted(root.rglob("*_contrast.tsv")):
        cols = None
        with path.open("r", encoding="utf-8") as f:
            for raw in f:
                if raw.startswith("#columns:"):
                    cols = raw.rstrip("\n")[len("#columns:"):].split("\t")
                    break
        if not cols:
            continue
        try:
            tip_i = cols.index("Tip")
            jp_i = cols.index("JP")
        except ValueError:
            continue
        with path.open("r", encoding="utf-8") as f:
            for lineno, raw in enumerate(f, 1):
                line = raw.rstrip("\n")
                if not line or line.startswith("#"):
                    continue
                parts = line.split("\t")
                if len(parts) <= tip_i:
                    continue
                tip = parts[tip_i]
                rs = reasons(tip)
                if rs:
                    hits.append({
                        "path": str(path),
                        "line": lineno,
                        "jp": parts[jp_i] if len(parts) > jp_i else "",
                        "tip": tip,
                        "reasons": rs,
                    })
    return hits


def main() -> int:
    hits = detect(ROOT)
    print(f"# A2 garbled-Tip hits: {len(hits)}")
    for h in hits:
        print(f"{h['path']}:{h['line']}\treasons={','.join(h['reasons'])}\tJP={h['jp']}\tTip={h['tip']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
