#!/usr/bin/env python3
"""
Phase-4: sync per-row Production[Why] into Recognition[MainUse].

The 2026-05-19 audit found that 94% of 5-row Recognition files have
identical Label/Formula/MainUse/Contrast across all rows — only QuickCue
varies. The "5 atomic exemplars" design collapses to "5 fronts + 1 back"
plus a small per-row hook.

This fixer copies Production's per-row `Why` field into Recognition's
per-row `MainUse` field for every Recognition row whose JP matches a
Production Sample. After the sync, the back-side reads:

  Label    (file-level grammar identity — kept)
  Formula  (file-level morphological pattern — kept)
  MainUse  (PER-ROW sense / pedagogical note — newly populated from Why)
  QuickCue (per-row contextual hook — kept)
  Contrast (file-level grammar comparison — kept)

Files where the JP↔Sample mapping is partial (some rows match, others
don't) are still synced for the matching rows; the others keep their
existing MainUse.

Files where Production doesn't exist or has no Why column are skipped.

Usage:  python3 scripts/_phase4_recognition_mainuse_sync.py [--dry-run]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

GRAMMAR_DIR = Path("grammar-strict")


def parse_tsv(path: Path):
    lines = path.read_text(encoding="utf-8").splitlines()
    cols = None
    header_end = 0
    for i, l in enumerate(lines):
        if l.startswith("#columns:"):
            cols = l[len("#columns:"):].split("\t")
        if l.startswith("#"):
            header_end = i + 1
        elif l.strip() == "":
            header_end = i + 1
            break
    if not cols:
        return None, [], []
    rows = []
    for l in lines:
        if not l.strip() or l.startswith("#"):
            continue
        parts = l.split("\t")
        # tolerate short rows
        while len(parts) < len(cols):
            parts.append("")
        rows.append(parts)
    return cols, rows, lines


def fix_file(rec_path: Path, dry_run: bool) -> tuple[int, int]:
    """Return (rows_synced, rows_unmatched)."""
    slug = rec_path.stem.replace("_recognition", "")
    prod_path = rec_path.parent / f"{slug}_production.tsv"
    if not prod_path.exists():
        return 0, 0

    rec_cols, rec_rows, rec_lines = parse_tsv(rec_path)
    prod_cols, prod_rows, _ = parse_tsv(prod_path)
    if not rec_cols or not prod_cols:
        return 0, 0
    if "JP" not in rec_cols or "MainUse" not in rec_cols:
        return 0, 0
    if "Sample" not in prod_cols or "Why" not in prod_cols:
        return 0, 0

    jp_idx = rec_cols.index("JP")
    mu_idx = rec_cols.index("MainUse")
    sample_idx = prod_cols.index("Sample")
    why_idx = prod_cols.index("Why")

    # Build sample → why map (use the first Why if duplicates)
    why_by_sample: dict[str, str] = {}
    for prow in prod_rows:
        sample = prow[sample_idx]
        why = prow[why_idx]
        if sample and why and sample not in why_by_sample:
            why_by_sample[sample] = why

    if not why_by_sample:
        return 0, 0

    # Walk recognition rows in original line order
    synced = unmatched = 0
    new_lines: list[str] = []
    row_iter = iter(rec_rows)
    for raw in rec_lines:
        if not raw.strip() or raw.startswith("#"):
            new_lines.append(raw + "\n")
            continue
        parts = next(row_iter, None)
        if parts is None:
            new_lines.append(raw + "\n")
            continue
        jp = parts[jp_idx] if len(parts) > jp_idx else ""
        if jp in why_by_sample:
            new_why = why_by_sample[jp]
            if parts[mu_idx] != new_why:
                parts[mu_idx] = new_why
                synced += 1
            # already-matching: don't count as sync
        else:
            unmatched += 1
        new_lines.append("\t".join(parts) + "\n")

    if synced > 0 and not dry_run:
        rec_path.write_text("".join(new_lines), encoding="utf-8")

    return synced, unmatched


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync Production Why → Recognition MainUse")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    total_synced = total_unmatched = files_touched = 0
    for rec in sorted(GRAMMAR_DIR.rglob("*_recognition.tsv")):
        synced, unmatched = fix_file(rec, args.dry_run)
        total_synced += synced
        total_unmatched += unmatched
        if synced > 0:
            files_touched += 1

    mode = "[DRY RUN] " if args.dry_run else ""
    print(f"{mode}Files touched: {files_touched}")
    print(f"{mode}Recognition rows synced (MainUse ← Production Why): {total_synced}")
    print(f"{mode}Recognition rows with no Production match (MainUse kept): {total_unmatched}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
