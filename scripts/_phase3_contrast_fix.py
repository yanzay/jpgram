#!/usr/bin/env python3
"""
Phase-3 contrast remediation — convert genuine spot-the-answer rows to
fill-in-blank format.

Two distinct contrast patterns coexist in grammar-strict/:

1. **Slash-format** (preserved):  JP contains "OptionA / OptionB" — both
   choices appear in the JP separated by " / ". This is a sound forced-
   choice design. Skip these rows.

2. **Single-form spot-the-answer** (fixed): JP shows the answer as a
   normal sentence; OptionA/B are alternatives but the answer is literally
   visible in the JP. Convert by replacing the first occurrence of Answer
   in JP with "___".

Heuristic:
- Skip if `OptionA / OptionB` (or `OptionB / OptionA`) appears in JP.
- Skip if Answer is not a substring of JP.
- Skip if Answer is empty or trivial (1 char, common particle).
- Skip if " / " in JP (slash-format already used).
- Otherwise: replace JP's first Answer occurrence with `___`.

Usage:  python3 scripts/_phase3_contrast_fix.py [--dry-run]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

GRAMMAR_DIR = Path("grammar-strict")


def fix_file(path: Path, dry_run: bool) -> tuple[int, int, list[str]]:
    """Return (rows_converted, rows_skipped_slash, log_lines)."""
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    cols = None
    for raw in lines:
        if raw.startswith("#columns:"):
            cols = raw[len("#columns:"):].rstrip("\n").split("\t")
            break
    if not cols or "JP" not in cols or "OptionA" not in cols \
       or "OptionB" not in cols or "Answer" not in cols:
        return 0, 0, []

    jp_idx = cols.index("JP")
    a_idx = cols.index("OptionA")
    b_idx = cols.index("OptionB")
    ans_idx = cols.index("Answer")

    converted = skipped_slash = 0
    log: list[str] = []
    new_lines: list[str] = []
    for raw in lines:
        if not raw.strip() or raw.startswith("#"):
            new_lines.append(raw)
            continue
        row = raw.rstrip("\n").split("\t")
        if len(row) <= max(jp_idx, a_idx, b_idx, ans_idx):
            new_lines.append(raw)
            continue
        jp = row[jp_idx]
        a = row[a_idx]
        b = row[b_idx]
        ans = row[ans_idx]

        # Skip if already a fill-in-blank
        if "___" in jp or "＿＿＿" in jp:
            new_lines.append(raw)
            continue

        # Skip if Answer is empty.
        if not ans:
            new_lines.append(raw)
            continue

        # If Answer is 1 char (common particle), only convert if it
        # appears exactly once in JP — otherwise we can't reliably
        # blank the *target* occurrence.
        if len(ans) < 2 and jp.count(ans) != 1:
            new_lines.append(raw)
            continue

        # Skip slash-format: both A and B appear separated by " / "
        if a in jp and b in jp and (f"{a} / {b}" in jp or f"{b} / {a}" in jp
                                     or f"{a}／{b}" in jp or f"{b}／{a}" in jp):
            skipped_slash += 1
            new_lines.append(raw)
            continue

        # Skip if Answer isn't a substring of JP
        if ans not in jp:
            new_lines.append(raw)
            continue

        # Skip if Answer == JP (whole-JP-is-answer pattern: the card asks
        # "is this sentence the right form?"; replacing the whole JP with ___
        # would make it unanswerable).
        if ans.strip() == jp.strip():
            new_lines.append(raw)
            continue

        # Skip if removing the answer leaves a JP shorter than 3 mora —
        # too little context for the learner to even guess.
        if len(jp) - len(ans) < 3:
            new_lines.append(raw)
            continue

        # Skip meta-comparison rows where JP itself is a study headline,
        # not a real Japanese sentence (e.g. `誰 vs 何違い`).
        if " vs " in jp or "違い" in jp:
            new_lines.append(raw)
            continue

        # Skip "X vs Y" forms without spaces (causative_contrast pattern).
        # If JP contains "vs" *and* both A and B appear in JP, it's already
        # a forced-choice form between A and B; replacing one of them
        # creates a malformed sentence.
        if "vs" in jp and a in jp and b in jp:
            skipped_slash += 1
            new_lines.append(raw)
            continue

        # Convert: replace FIRST occurrence of Answer with ___
        new_jp = jp.replace(ans, "___", 1)
        row[jp_idx] = new_jp
        log.append(f"  FIX {path.name}: {jp[:50]!r}\n      → {new_jp[:50]!r}  (Answer={ans!r})")
        eol = "\r\n" if raw.endswith("\r\n") else "\n"
        new_lines.append("\t".join(row) + eol)
        converted += 1

    if converted > 0 and not dry_run:
        path.write_text("".join(new_lines), encoding="utf-8")

    return converted, skipped_slash, log


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert spot-the-answer contrast rows to fill-in-blank")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    total_fixed = total_skipped_slash = 0
    for tsv in sorted(GRAMMAR_DIR.rglob("*_contrast.tsv")):
        fixed, skipped, log = fix_file(tsv, args.dry_run)
        total_fixed += fixed
        total_skipped_slash += skipped
        for ln in log:
            print(ln)

    mode = "[DRY RUN] " if args.dry_run else ""
    print(f"\n{mode}Converted: {total_fixed} row(s) to ___-blank format")
    print(f"{mode}Skipped (slash-format A / B in JP): {total_skipped_slash} row(s) — preserved as forced-choice design")
    return 0


if __name__ == "__main__":
    sys.exit(main())
