#!/usr/bin/env python3
"""
Fix Reading column in production/recognition TSVs where the current reading
fails the Phase-1 lint (kanji, Arabic digits, ℃/°, sokuon doubling).

For each bad row, regenerates the reading from the JP source column using
the updated scripts/jp_reading.py pipeline. Only updates rows whose current
reading has issues AND whose regenerated reading is clean; logs rows where
the fix itself is dirty so they can be hand-curated.

Usage:
    python3 scripts/fix_reading_column.py [--dry-run]
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from jp_reading import bad_reading_issues, reading as gen_reading

GRAMMAR_DIR = Path("grammar-strict")

# Which column provides the JP source for each note type.
_JP_SOURCE: dict[str, str] = {
    "Recognition": "JP",
    "Production":  "Sample",
    "Dictation":   "Answer",
    "Listening":   "Transcript",
}


def _detect_note_type(path: Path) -> str:
    name = path.stem.lower()
    if "recognition" in name: return "Recognition"
    if "production"  in name: return "Production"
    if "cloze"       in name: return "Cloze"
    if "contrast"    in name: return "Contrast"
    if "listening"   in name: return "Listening"
    if "dictation"   in name: return "Dictation"
    return "Recognition"


def fix_file(path: Path, dry_run: bool) -> tuple[int, int]:
    """Return (rows_fixed, rows_unfixable)."""
    nt = _detect_note_type(path)
    if nt not in _JP_SOURCE:
        return 0, 0

    text = path.read_text(encoding="utf-8")
    raw_lines = text.splitlines(keepends=True)

    header_cols: list[str] | None = None
    for raw in raw_lines:
        if raw.startswith("#columns:"):
            header_cols = raw.rstrip("\n").lstrip("#columns:").split("\t")
            # re-parse properly
            header_cols = raw.rstrip("\n")[len("#columns:"):].split("\t")
            break

    if header_cols is None or "Reading" not in header_cols:
        return 0, 0

    reading_idx = header_cols.index("Reading")
    source_col = _JP_SOURCE[nt]
    if source_col not in header_cols:
        return 0, 0
    source_idx = header_cols.index(source_col)

    fixed = unfixable = 0
    new_lines: list[str] = []
    for raw in raw_lines:
        if not raw.strip() or raw.startswith("#"):
            new_lines.append(raw)
            continue
        row = next(csv.reader([raw.rstrip("\n")], delimiter="\t", quotechar='"'))
        if len(row) != len(header_cols):
            new_lines.append(raw)
            continue

        current_reading = row[reading_idx]
        issues = bad_reading_issues(current_reading)
        if not issues:
            new_lines.append(raw)
            continue

        # Regenerate from JP source
        jp_source = row[source_idx]
        if not jp_source.strip():
            new_lines.append(raw)
            unfixable += 1
            continue

        new_reading = gen_reading(jp_source)
        new_issues = bad_reading_issues(new_reading)
        if new_issues:
            print(f"  UNFIXABLE {path.name}:{raw_lines.index(raw)+1}: "
                  f"regen still dirty: {new_issues} → {new_reading[:50]!r}")
            new_lines.append(raw)
            unfixable += 1
            continue

        print(f"  FIX {path.name}: {current_reading[:35]!r} → {new_reading[:35]!r}")
        row[reading_idx] = new_reading
        # Rebuild line preserving trailing newline style
        eol = "\r\n" if raw.endswith("\r\n") else "\n"
        new_raw = "\t".join(row) + eol
        new_lines.append(new_raw)
        fixed += 1

    if fixed > 0 and not dry_run:
        path.write_text("".join(new_lines), encoding="utf-8")

    return fixed, unfixable


def main() -> int:
    parser = argparse.ArgumentParser(description="Fix Reading column in TSVs")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print fixes without writing files")
    args = parser.parse_args()

    tsvs = sorted(GRAMMAR_DIR.rglob("*_production.tsv")) + \
           sorted(GRAMMAR_DIR.rglob("*_recognition.tsv")) + \
           sorted(GRAMMAR_DIR.rglob("*_dictation.tsv")) + \
           sorted(GRAMMAR_DIR.rglob("*_listening.tsv"))

    total_fixed = total_unfixable = 0
    for tsv in tsvs:
        fixed, unfixable = fix_file(tsv, args.dry_run)
        total_fixed += fixed
        total_unfixable += unfixable

    mode = "[DRY RUN] " if args.dry_run else ""
    print(f"\n{mode}Fixed: {total_fixed}  |  Unfixable (needs manual review): {total_unfixable}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
