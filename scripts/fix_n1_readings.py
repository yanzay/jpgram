#!/usr/bin/env python3
"""N1 native-pass reading fixes — substring replacements scoped to the
specific defective sentences found by the audit.

Each tuple is (wrong_substring, correct_substring). The substrings are
chosen to be unique enough that they won't fire on unrelated rows.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "grammar-strict"

REPLACEMENTS = [
    # ばこそ + とあれば: 何でも → なんでも (deck-wide, but conservative scope)
    ("けんこうであればこそ、なにでもできる", "けんこうであればこそ、なんでもできる"),
    ("きみのためとあれば、なにでもやる", "きみのためとあれば、なんでもやる"),
    # と思いきや: 瞬く間に → またたくまに
    ("しばたたくあいだに", "またたくまに"),
    # なりとも: 何なりとも → なんなりとも
    ("なになりとも", "なんなりとも"),
    # というところ: 二日 → ふつか
    ("あとふたかあれば", "あとふつかあれば"),
    # ゆえに: 我 → われ
    ("わがおもう、ゆえにわがあり", "われおもう、ゆえにわれあり"),
    # 如何: 状況如何 → じょうきょういかん
    ("じっしするかどうかはじょうきょういかがだ", "じっしするかどうかはじょうきょういかんだ"),
]


def fix_file(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    fixed = text
    hits = 0
    for wrong, right in REPLACEMENTS:
        if wrong in fixed:
            fixed = fixed.replace(wrong, right)
            hits += 1
    if fixed != text:
        path.write_text(fixed, encoding="utf-8")
    return hits


if __name__ == "__main__":
    total = 0
    files_changed = 0
    for tsv in sorted(ROOT.rglob("*.tsv")):
        n = fix_file(tsv)
        if n:
            total += n
            files_changed += 1
            print(f"{tsv.relative_to(ROOT.parent)}: {n} replacement(s)")
    print(f"\nTotal: {total} replacement(s) across {files_changed} file(s).")
