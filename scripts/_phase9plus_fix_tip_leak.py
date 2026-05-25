#!/usr/bin/env python3
"""
Phase-9++ — strip the "Tip=Answer" leak pattern from contrast files.

The 2026-05-25 EN re-audit found 167 contrast rows where the Tip column
literally states the answer string (e.g., `Tip="permission=てもいい"`
when the answer is てもいい). This defeats the contrast card's purpose.

Fix: replace the literal answer occurrence in the Tip with a generic
"this form" or "→" marker so the Tip still teaches the discriminator
but doesn't give away the answer.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

GRAMMAR_DIR = Path("grammar-strict")


def fix_tip(tip: str, answer: str) -> str:
    """If the literal answer appears in the Tip, replace it with a marker."""
    if not answer or len(answer) < 2 or answer not in tip:
        return tip
    # Replace `=answer` with `→ this form`
    # First normalize: collapse whitespace
    new = tip.replace(f"={answer}", "")
    new = new.replace(f"= {answer}", "")
    new = new.replace(f" {answer}", " (this form)")
    new = new.replace(f"{answer} ", "(this form) ")
    new = new.replace(answer, "(this form)")
    # Clean up double spaces / trailing semicolons
    new = " ".join(new.split())
    new = new.rstrip(";").rstrip(",").rstrip(":")
    return new


def fix_file(path: Path, dry_run: bool) -> int:
    """Return number of rows fixed."""
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    cols = None
    for raw in lines:
        if raw.startswith("#columns:"):
            cols = raw[len("#columns:"):].rstrip("\n").split("\t")
            break
    if not cols or "Tip" not in cols or "Answer" not in cols:
        return 0
    tip_idx = cols.index("Tip")
    ans_idx = cols.index("Answer")

    fixed = 0
    new_lines = []
    for raw in lines:
        if not raw.strip() or raw.startswith("#"):
            new_lines.append(raw)
            continue
        eol = "\r\n" if raw.endswith("\r\n") else "\n"
        parts = raw.rstrip("\n").rstrip("\r").split("\t")
        if len(parts) <= max(tip_idx, ans_idx):
            new_lines.append(raw)
            continue
        new_tip = fix_tip(parts[tip_idx], parts[ans_idx])
        if new_tip != parts[tip_idx]:
            parts[tip_idx] = new_tip
            new_lines.append("\t".join(parts) + eol)
            fixed += 1
        else:
            new_lines.append(raw)

    if fixed > 0 and not dry_run:
        path.write_text("".join(new_lines), encoding="utf-8")
    return fixed


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    total = files = 0
    for tsv in sorted(GRAMMAR_DIR.rglob("*_contrast.tsv")):
        n = fix_file(tsv, args.dry_run)
        if n > 0:
            total += n
            files += 1
            print(f"  FIXED {n} rows in {tsv.name}")
    mode = "[DRY RUN] " if args.dry_run else ""
    print(f"\n{mode}Total: {total} Tip-leak rows fixed across {files} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
