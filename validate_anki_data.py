#!/usr/bin/env python3
"""
Validates every TSV under ./grammar/ against the schema declared in
build_anki_package.NOTE_TYPES.

Checks:
  * `#columns:` header is present and matches the corresponding NOTE_TYPE
  * every data row has exactly len(header) tab-separated fields
  * Recognition / Contrast / Production / Cloze first column is non-empty
  * tags column is well-formed (space-separated tokens, no commas)
  * cloze rows contain at least one {{c…::…}} marker
  * no duplicate rows (within a file) by sentence+target

Exit code: 0 if clean, 1 on any error.
"""
from __future__ import annotations

import csv
import re
import sys
from collections import Counter
from pathlib import Path

from build_anki_package import NOTE_TYPES, detect_note_type

GRAMMAR_DIR = Path("grammar")
_CLOZE_RE = re.compile(r"\{\{c\d+::[^}]+\}\}")


def lint_file(path: Path) -> list[str]:
    errs: list[str] = []
    nt = detect_note_type(path)
    expected = NOTE_TYPES[nt]
    text = path.read_text(encoding="utf-8")
    header = None
    data = []
    for ln, raw in enumerate(text.splitlines(), 1):
        if raw.startswith("#columns:"):
            header = raw[len("#columns:"):].split("\t")
            continue
        if not raw or raw.startswith("#"):
            continue
        data.append((ln, raw))

    if header is None:
        errs.append(f"{path}: missing `#columns:` header")
        return errs
    if header != expected:
        errs.append(f"{path}: header {header} != expected {expected} (note type {nt})")

    seen: Counter[str] = Counter()
    for ln, raw in data:
        row = next(csv.reader([raw], delimiter="\t", quotechar='"'))
        if len(row) != len(expected):
            errs.append(f"{path}:{ln}: {len(row)} fields, expected {len(expected)}")
            continue
        if not row[0].strip():
            errs.append(f"{path}:{ln}: first field empty")
        if nt == "Cloze" and not _CLOZE_RE.search(row[0]):
            errs.append(f"{path}:{ln}: cloze row has no {{c…::…}} marker")
        # Tags column is the last one in every note type.
        tags = row[-1].strip()
        if "," in tags:
            errs.append(f"{path}:{ln}: comma in tags — Anki uses spaces")
        key = (row[0], row[1] if len(row) > 1 else "")
        seen[key] += 1
    for key, n in seen.items():
        if n > 1:
            errs.append(f"{path}: duplicate row × {n}: {key[0][:40]}…")
    return errs


def main():
    if not GRAMMAR_DIR.exists():
        print("grammar/ does not exist yet — nothing to validate.")
        return 0
    all_errs: list[str] = []
    files = sorted(GRAMMAR_DIR.rglob("*.tsv"))
    for f in files:
        all_errs.extend(lint_file(f))
    if not all_errs:
        print(f"✓ {len(files)} TSV file(s) clean.")
        return 0
    for e in all_errs:
        print(e)
    print(f"\n✗ {len(all_errs)} error(s) across {len(files)} file(s).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
