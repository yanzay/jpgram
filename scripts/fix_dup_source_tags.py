#!/usr/bin/env python3
"""When a row has both `source:authored` and `source:<other>` (e.g.,
shin-kanzen, curated-jpgram), drop `source:authored` and keep the more
specific source. Also handles other duplicate-prefix patterns.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent / "grammar-strict"


def dedupe_tags(tag_str: str) -> str:
    """Dedupe tag prefixes. For source:, prefer non-'authored' values.
    For other prefixes, keep the first occurrence."""
    tokens = tag_str.split()
    by_prefix: dict[str, list[str]] = {}
    order: list[str] = []
    for tok in tokens:
        if ":" in tok:
            prefix = tok.split(":", 1)[0]
        else:
            prefix = tok
        if prefix not in by_prefix:
            by_prefix[prefix] = []
            order.append(prefix)
        by_prefix[prefix].append(tok)
    out: list[str] = []
    for prefix in order:
        vals = by_prefix[prefix]
        if len(vals) == 1:
            out.append(vals[0])
            continue
        # Duplicate. For source: prefer non-authored.
        if prefix == "source":
            non_authored = [v for v in vals if v != "source:authored"]
            if non_authored:
                out.append(non_authored[0])  # keep first non-authored
            else:
                out.append(vals[0])
        elif prefix == "complexity":
            # complexity:intro is the most specific level normally seen first
            # keep the first one for stability
            out.append(vals[0])
        else:
            # default: keep first occurrence
            out.append(vals[0])
    return " ".join(out)


def process_file(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    changes = 0
    for i, line in enumerate(lines):
        if line.startswith("#") or not line.strip():
            continue
        parts = line.rstrip("\n").split("\t")
        if len(parts) < 2:
            continue
        # The Tags column is always the last one.
        tags = parts[-1]
        # Check for any duplicate prefix
        prefixes = [t.split(":", 1)[0] for t in tags.split() if t]
        if len(prefixes) == len(set(prefixes)):
            continue
        new_tags = dedupe_tags(tags)
        if new_tags != tags:
            parts[-1] = new_tags
            lines[i] = "\t".join(parts) + ("\n" if line.endswith("\n") else "")
            changes += 1
    if changes:
        path.write_text("".join(lines), encoding="utf-8")
    return changes


if __name__ == "__main__":
    total = 0
    files_changed = 0
    for tsv in sorted(ROOT.rglob("*.tsv")):
        n = process_file(tsv)
        if n:
            total += n
            files_changed += 1
    print(f"Fixed {total} rows across {files_changed} files.")
