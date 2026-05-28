#!/usr/bin/env python3
"""One-shot fix for 中=ちゅう vs じゅう reading bug across the deck.

In time-window and spatial-extent compounds (今日中, 今週中, 今月中,
今年中, 世界中, 国中, 町中, etc.), 中 reads じゅう, not ちゅう. The
ちゅう reading is for "in the middle of an action" (工事中, 会議中).

This script flips ちゅう → じゅう ONLY in the Reading columns where the
preceding noun is one of the time-window/spatial-extent set.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "grammar-strict"

REPLACEMENTS = [
    ("きょうちゅう", "きょうじゅう"),
    ("こんしゅうちゅう", "こんしゅうじゅう"),
    ("こんげつちゅう", "こんげつじゅう"),
    ("ことしちゅう", "ことしじゅう"),
    ("せかいちゅう", "せかいじゅう"),
    ("くにちゅう", "くにじゅう"),
    ("まちちゅう", "まちじゅう"),
    ("いえちゅう", "いえじゅう"),
    ("いちにちちゅう", "いちにちじゅう"),
    ("いちねんちゅう", "いちねんじゅう"),
]

def fix_file(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    fixed = text
    for wrong, right in REPLACEMENTS:
        fixed = fixed.replace(wrong, right)
    if fixed != text:
        path.write_text(fixed, encoding="utf-8")
        # Count the diffs
        return sum(text.count(w) for w, _ in REPLACEMENTS)
    return 0

if __name__ == "__main__":
    total = 0
    files_changed = 0
    for tsv in sorted(ROOT.rglob("*.tsv")):
        n = fix_file(tsv)
        if n:
            total += n
            files_changed += 1
            print(f"{tsv.relative_to(ROOT.parent)}: {n} occurrence(s)")
    print(f"\nTotal: {total} occurrence(s) fixed across {files_changed} file(s).")
