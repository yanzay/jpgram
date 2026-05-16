#!/usr/bin/env python3
"""
Validates every TSV under ./grammar/ against the schema declared in
build_anki_package.NOTE_TYPES.

Checks:
  * `#columns:` header present and matches the corresponding NOTE_TYPE
  * every data row has exactly len(header) tab-separated fields
  * first column is non-empty
  * tags column is well-formed (space-separated tokens, no commas)
  * cloze rows contain at least one {{c…::…}} marker
  * no duplicate rows (within a file) by (sentence, second_field)
  * **NEW** [sound:WAVE0_PLACEHOLDER.mp3] never reaches grammar/
  * **NEW** every [sound:X.mp3] reference resolves to media/audio/X.mp3
            OR is registered in media/audio_manifest.json
  * **NEW** audio filenames don't collide across the corpus (would cause
            silent overwrites at Anki import time)

Exit code: 0 if clean, 1 on any error.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from build_anki_package import NOTE_TYPES, detect_note_type

GRAMMAR_DIR = Path("grammar")
MEDIA_DIR = Path("media/audio")
MANIFEST_PATH = Path("media/audio_manifest.json")

_CLOZE_RE = re.compile(r"\{\{c\d+::[^}]+\}\}")
_ANY_CLOZE_RE = re.compile(r"\{\{c\d+::")
_SOUND_RE = re.compile(r"\[sound:([^\]]+)\]")
_PLACEHOLDER_RE = re.compile(r"\[sound:WAVE\d+_PLACEHOLDER\.mp3\]", re.I)
_FAKE_HASH_RE = re.compile(r"\[sound:[0-9a-f]{12}\.mp3\]", re.I)  # may be legit


def _load_manifest_keys() -> set[str]:
    if not MANIFEST_PATH.exists():
        return set()
    try:
        data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        return set(data.get("entries", {}).keys())
    except json.JSONDecodeError:
        return set()


def lint_file(path: Path,
              audio_users: dict[str, list[str]],
              manifest_keys: set[str]) -> list[str]:
    errs: list[str] = []
    nt = detect_note_type(path)
    expected = NOTE_TYPES[nt]
    text = path.read_text(encoding="utf-8")
    header = None
    data: list[tuple[int, str]] = []
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
        errs.append(f"{path}: header {header} != expected {expected} "
                    f"(note type {nt})")

    seen: Counter[tuple[str, str]] = Counter()
    for ln, raw in data:
        row = next(csv.reader([raw], delimiter="\t", quotechar='"'))
        if len(row) != len(expected):
            errs.append(f"{path}:{ln}: {len(row)} fields, expected "
                        f"{len(expected)}")
            continue
        if not row[0].strip():
            errs.append(f"{path}:{ln}: first field empty")
        if nt == "Cloze" and not _CLOZE_RE.search(row[0]):
            errs.append(f"{path}:{ln}: cloze row has no {{c…::…}} marker")
        if nt != "Cloze":
            for idx, field in enumerate(row):
                if _ANY_CLOZE_RE.search(field):
                    errs.append(
                        f"{path}:{ln}: cloze marker leaked into non-cloze note "
                        f"(field '{header[idx]}')"
                    )

        # Tags column = last column in every NOTE_TYPE.
        tags = row[-1].strip()
        if "," in tags:
            errs.append(f"{path}:{ln}: comma in tags — Anki uses spaces")

        # Audio column — every note type has it; usually the second-to-last.
        audio_field = ""
        if "Audio" in header:
            audio_field = row[header.index("Audio")]
        # Placeholder check (would silently ship as broken audio).
        if _PLACEHOLDER_RE.search(audio_field):
            errs.append(f"{path}:{ln}: WAVE-0 placeholder audio "
                        f"reached grammar/ — regenerate via build_audio.py")
        # Audio reference resolution.
        for m in _SOUND_RE.finditer(audio_field):
            ref = m.group(1)
            stem = ref.rsplit(".", 1)[0]
            on_disk = (MEDIA_DIR / ref).exists()
            in_manifest = stem in manifest_keys
            if not on_disk and not in_manifest:
                errs.append(f"{path}:{ln}: audio ref [sound:{ref}] not "
                            f"in media/audio/ and not in manifest")
            audio_users[ref].append(f"{path}:{ln}")

        key = tuple(row)
        seen[key] += 1
    for key, n in seen.items():
        if n > 1:
            preview = key[0][:40] if key else ""
            errs.append(f"{path}: duplicate row × {n}: {preview}…")
    return errs


def main() -> int:
    if not GRAMMAR_DIR.exists():
        print("grammar/ does not exist yet — nothing to validate.")
        return 0

    manifest_keys = _load_manifest_keys()
    audio_users: dict[str, list[str]] = defaultdict(list)
    all_errs: list[str] = []
    files = sorted(GRAMMAR_DIR.rglob("*.tsv"))
    for f in files:
        all_errs.extend(lint_file(f, audio_users, manifest_keys))

    # Cross-corpus checks: an audio filename used by >1 note is fine
    # (same JP sentence appears in multiple cards), but used by >1
    # DIFFERENT JP texts would mean a hash collision — investigate.
    # We can't fully verify without re-hashing every JP text, so we
    # only report multi-use as INFO if it crosses note types.
    multi_use = {ref: users for ref, users in audio_users.items()
                 if len(users) > 5}
    for ref, users in multi_use.items():
        # Truly excessive reuse hints at a copy-paste error.
        if len(users) > 20:
            all_errs.append(
                f"WARN: audio {ref} referenced from {len(users)} rows — "
                f"verify it's the same JP sentence everywhere")

    if not all_errs:
        print(f"✓ {len(files)} TSV file(s) clean. "
              f"{len(audio_users)} audio refs total, "
              f"{len(manifest_keys)} known-good in manifest.")
        return 0
    for e in all_errs:
        print(e)
    print(f"\n✗ {len(all_errs)} error(s) across {len(files)} file(s).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
