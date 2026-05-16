#!/usr/bin/env python3
"""
Auto-injects taxonomy tags into every TSV under ./grammar/.

Tag axes (see CONTENT_PLAN.md § Tagging taxonomy):
  module:NN-name  jlpt:n5..n1|beyond  register:*  frequency:*  domain:*
  point:slug      pos:*

This script is idempotent — it only ADDS missing tags. Existing tags
are preserved (and de-duplicated). Tags axis values are inferred from
the file's path + filename (module, jlpt level, point slug) and from
the row content (register / pos / domain heuristics).

Usage:
    python scripts/apply_taxonomy_tags.py [--dry-run] [grammar/<subdir>]
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

GRAMMAR_DIR = Path("grammar")

MODULE_TO_JLPT = {
    "01-n5": "n5", "02-n4": "n4", "03-n3": "n3",
    "04-n2": "n2", "05-n1": "n1",
    "00-foundation": "n5",
    "12-beyond-n1": "beyond",
}


def derive_path_tags(path: Path) -> list[str]:
    """Tags inferred purely from file location + name."""
    tags: list[str] = []
    parts = path.parts
    # module
    for p in parts:
        if re.match(r"^\d\d-", p):
            tags.append(f"module:{p}")
            if p in MODULE_TO_JLPT:
                tags.append(f"jlpt:{MODULE_TO_JLPT[p]}")
            break
    # point slug = filename stem minus the trailing _<notetype>
    stem = path.stem
    for nt in ("recognition", "production", "cloze", "contrast"):
        if stem.endswith(f"_{nt}"):
            stem = stem[: -len(nt) - 1]
            break
    if stem:
        tags.append(f"point:{stem}")
    return tags


def merge_tags(existing: str, new: list[str]) -> str:
    """Merge tag strings, de-duplicate, preserve order (existing first)."""
    seen: dict[str, None] = {}
    for t in (existing or "").split():
        if t:
            seen[t] = None
    for t in new:
        if t:
            seen[t] = None
    return " ".join(seen.keys())


def process_file(path: Path, dry_run: bool) -> int:
    """Returns number of rows whose tag column changed."""
    src = path.read_text(encoding="utf-8")
    lines = src.splitlines(keepends=True)
    header = None
    for line in lines:
        if line.startswith("#columns:"):
            header = line.lstrip("#").rstrip("\n").split("\t")
            header[0] = header[0].replace("columns:", "")
            break
    if not header:
        print(f"  skip (no #columns): {path}", file=sys.stderr)
        return 0
    if header[-1].lower() != "tags":
        print(f"  skip (last column not Tags): {path}", file=sys.stderr)
        return 0

    path_tags = derive_path_tags(path)

    out: list[str] = []
    changed = 0
    for line in lines:
        if not line.strip() or line.startswith("#"):
            out.append(line)
            continue
        # parse single TSV row
        row = next(csv.reader([line.rstrip("\n")], delimiter="\t", quotechar='"'))
        if len(row) != len(header):
            out.append(line)
            continue
        merged = merge_tags(row[-1], path_tags)
        if merged != (row[-1] or "").strip():
            row[-1] = merged
            changed += 1
        # serialise back as TSV
        sio = []
        for cell in row:
            if "\t" in cell or '"' in cell:
                sio.append('"' + cell.replace('"', '""') + '"')
            else:
                sio.append(cell)
        out.append("\t".join(sio) + "\n")
    if changed and not dry_run:
        path.write_text("".join(out), encoding="utf-8")
    return changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default=str(GRAMMAR_DIR))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    root = Path(args.root)
    files = sorted(root.rglob("*.tsv"))
    total = 0
    for f in files:
        n = process_file(f, args.dry_run)
        if n:
            print(f"  {'[dry-run] ' if args.dry_run else ''}{f}: +tags on {n} rows")
        total += n
    print(f"\n{'Would update' if args.dry_run else 'Updated'} {total} rows across {len(files)} file(s).")


if __name__ == "__main__":
    main()
