#!/usr/bin/env python3
"""
Fill in [sound:HASH.mp3] references for rows that were marked
scaffold:pending-audio. After build_audio.py generates the MP3s,
this script walks each TSV, computes sha1(JP_source)[:12] per row,
and writes the audio ref into the Audio column.

Removes the scaffold:pending-audio tag once the audio ref is set,
unless the audio file doesn't exist on disk.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import re
import sys
from pathlib import Path

GRAMMAR_DIR = Path("grammar-strict")
MEDIA_DIR = Path("media/audio")

_CLOZE_EXTRACT_RE = re.compile(r"\{\{c\d+::([^:}]+)(?:::[^}]+)?\}\}")


def audio_source(nt: str, header: list[str], row: list[str]) -> str:
    """Return the JP text that audio is hashed from (mirrors build_audio.py)."""
    if nt == "Production":
        idx = header.index("Sample") if "Sample" in header else 0
        return row[idx].strip()
    if nt == "Recognition":
        idx = header.index("JP") if "JP" in header else 0
        return row[idx].strip()
    if nt == "Cloze":
        idx = header.index("Text") if "Text" in header else 0
        text = row[idx].strip()
        return _CLOZE_EXTRACT_RE.sub(r"\1", text).strip()
    if nt == "Contrast":
        idx_jp = header.index("JP") if "JP" in header else 0
        idx_ans = header.index("Answer") if "Answer" in header else None
        jp = row[idx_jp].strip()
        ans = row[idx_ans].strip() if idx_ans is not None else ""
        return jp.replace("___", ans) if jp and ans else jp
    if nt == "Dictation":
        idx = header.index("Answer") if "Answer" in header else 0
        return row[idx].strip()
    if nt == "Listening":
        idx = header.index("Transcript") if "Transcript" in header else 0
        return row[idx].strip()
    return row[0].strip()


def sha1_12(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def fix_file(path: Path, dry_run: bool) -> tuple[int, int]:
    """Return (rows_filled, rows_audio_missing)."""
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    header = None
    nt = None
    for raw in lines:
        if raw.startswith("#columns:"):
            header = raw[len("#columns:"):].rstrip("\n").split("\t")
        elif raw.startswith("#notetype:"):
            nt = raw[len("#notetype:"):].rstrip("\n").strip()
    if header is None or nt is None:
        return 0, 0
    if "Audio" not in header or "Tags" not in header:
        return 0, 0

    audio_idx = header.index("Audio")
    tags_idx = header.index("Tags")

    filled = missing = 0
    new_lines = []
    for raw in lines:
        if not raw.strip() or raw.startswith("#"):
            new_lines.append(raw)
            continue
        eol = "\r\n" if raw.endswith("\r\n") else "\n"
        parts = raw.rstrip("\n").rstrip("\r").split("\t")
        if len(parts) <= max(audio_idx, tags_idx):
            new_lines.append(raw)
            continue
        tags = parts[tags_idx]
        if "scaffold:pending-audio" not in tags:
            new_lines.append(raw)
            continue

        # Compute audio hash from the source text
        src = audio_source(nt, header, parts)
        if not src:
            new_lines.append(raw)
            continue
        h = sha1_12(src)
        mp3 = MEDIA_DIR / f"{h}.mp3"
        if not mp3.exists():
            missing += 1
            new_lines.append(raw)
            continue

        # Update Audio column + drop scaffold:pending-audio tag
        parts[audio_idx] = f"[sound:{h}.mp3]"
        new_tags = " ".join(
            t for t in tags.split() if t != "scaffold:pending-audio"
        )
        parts[tags_idx] = new_tags
        new_lines.append("\t".join(parts) + eol)
        filled += 1

    if filled > 0 and not dry_run:
        path.write_text("".join(new_lines), encoding="utf-8")
    return filled, missing


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    total_filled = total_missing = 0
    files_touched = 0
    for tsv in sorted(GRAMMAR_DIR.rglob("*.tsv")):
        filled, missing = fix_file(tsv, args.dry_run)
        if filled or missing:
            if filled:
                files_touched += 1
            total_filled += filled
            total_missing += missing

    mode = "[DRY RUN] " if args.dry_run else ""
    print(f"{mode}Audio refs filled: {total_filled} rows in {files_touched} files")
    print(f"{mode}Pending rows where MP3 still missing: {total_missing}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
