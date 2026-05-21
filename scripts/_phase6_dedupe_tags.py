#!/usr/bin/env python3
"""
Phase-6 helper — de-duplicate tag-key occurrences per row.

For tags like `complexity:`, `frequency:`, `jlpt:`, `module:`, `point:`,
`source:`, keep only the FIRST occurrence per row. Anki indexes
duplicate-prefix tags as separate tags, which inflates filtered-deck
cardinality and breaks `jlpt:nX`-style filtering.

Usage:  python3 scripts/_phase6_dedupe_tags.py [--dry-run]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

GRAMMAR_DIR = Path("grammar-strict")
DEDUPE_PREFIXES = {"complexity", "frequency", "jlpt", "module", "point", "source"}


def dedupe_tags(tags_str: str) -> tuple[str, int]:
    """Return (deduplicated_tags_string, number_of_tokens_dropped)."""
    tokens = tags_str.split()
    seen_prefixes: set[str] = set()
    out: list[str] = []
    dropped = 0
    for tok in tokens:
        if ":" in tok:
            prefix = tok.split(":", 1)[0]
            if prefix in DEDUPE_PREFIXES and prefix in seen_prefixes:
                dropped += 1
                continue
            seen_prefixes.add(prefix)
        out.append(tok)
    return " ".join(out), dropped


def fix_file(path: Path, dry_run: bool) -> int:
    """Return number of tag-tokens dropped from this file."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    cols = None
    for raw in lines:
        if raw.startswith("#columns:"):
            cols = raw[len("#columns:"):].rstrip("\n").split("\t")
            break
    if not cols or "Tags" not in cols:
        return 0
    tags_idx = cols.index("Tags")

    total_dropped = 0
    new_lines: list[str] = []
    for raw in lines:
        if not raw.strip() or raw.startswith("#"):
            new_lines.append(raw)
            continue
        eol = "\r\n" if raw.endswith("\r\n") else "\n"
        parts = raw[:-len(eol) if raw.endswith(eol) else None].split("\t")
        if len(parts) <= tags_idx:
            new_lines.append(raw)
            continue
        new_tags, dropped = dedupe_tags(parts[tags_idx])
        total_dropped += dropped
        if dropped > 0:
            parts[tags_idx] = new_tags
            new_lines.append("\t".join(parts) + eol)
        else:
            new_lines.append(raw)

    if total_dropped > 0 and not dry_run:
        path.write_text("".join(new_lines), encoding="utf-8")
    return total_dropped


def main() -> int:
    parser = argparse.ArgumentParser(description="De-duplicate tag prefixes per row")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    total_dropped = 0
    files_touched = 0
    for tsv in sorted(GRAMMAR_DIR.rglob("*.tsv")):
        dropped = fix_file(tsv, args.dry_run)
        if dropped > 0:
            files_touched += 1
            total_dropped += dropped

    mode = "[DRY RUN] " if args.dry_run else ""
    print(f"{mode}Dropped {total_dropped} duplicate tag-tokens across {files_touched} files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
