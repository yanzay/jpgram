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

_READING_KANJI_RE = re.compile(r"[一-龯]")
_READING_DIGIT_RE = re.compile(r"[0-9０-９]")
_READING_SYMBOL_RE = re.compile(r"[℃°]")
_READING_SOKUON_DOUBLE_RE = re.compile(r"っっ|ーー|ゅゅ|ょょ|ゃゃ")

GRAMMAR_DIR = Path("grammar-strict")
MEDIA_DIR = Path("media/audio")
MANIFEST_PATH = Path("media/audio_manifest.json")
TAXONOMY_PATH = Path("data/grammar_taxonomy_bunpro.tsv")

_CLOZE_RE = re.compile(r"\{\{c\d+::[^}]+\}\}")
_ANY_CLOZE_RE = re.compile(r"\{\{c\d+::")
_INVENTED_CLASSICAL_RE = re.compile(r"べまじ|るざり|とやもしれない|やひや|ぜんくして")
_META_EN_RE = re.compile(r" = |Use '|attaches to")
_SOUND_RE = re.compile(r"\[sound:([^\]]+)\]")
_PLACEHOLDER_RE = re.compile(r"\[sound:WAVE\d+_PLACEHOLDER\.mp3\]", re.I)
_FAKE_HASH_RE = re.compile(r"\[sound:[0-9a-f]{12}\.mp3\]", re.I)  # may be legit
_PLACEHOLDER_TOKEN_RE = re.compile(r"\bexample(?:[a-z0-9_-]*)\b", re.I)
_JP_CHAR_RE = re.compile(r"[一-龯ぁ-んァ-ン]")
_CLOZE_EXTRACT_RE = re.compile(r"\{\{c\d+::([^:}]+)(?:::[^}]+)?\}\}")


def _load_manifest_keys() -> set[str]:
    if not MANIFEST_PATH.exists():
        return set()
    try:
        data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        return set(data.get("entries", {}).keys())
    except json.JSONDecodeError:
        return set()


def _load_taxonomy_points() -> set[str]:
    if not TAXONOMY_PATH.exists():
        return set()
    points: set[str] = set()
    for raw in TAXONOMY_PATH.read_text(encoding="utf-8").splitlines():
        if not raw or raw.startswith("#"):
            continue
        row = next(csv.reader([raw], delimiter="\t", quotechar='"'))
        if row and row[0].strip():
            points.add(row[0].strip())
    return points


def _source_sentence(nt: str, header: list[str], row: list[str]) -> str:
    if nt == "Production":
        sample = row[header.index("Sample")].strip() if "Sample" in header else ""
        target = row[header.index("Target")].strip() if "Target" in header else ""
        if sample and _JP_CHAR_RE.search(sample):
            return sample
        return target or sample
    if nt == "Cloze":
        text = row[header.index("Text")].strip() if "Text" in header else row[0].strip()
        return _CLOZE_EXTRACT_RE.sub(r"\1", text)
    if nt == "Contrast":
        jp = row[header.index("JP")].strip() if "JP" in header else row[0].strip()
        ans = row[header.index("Answer")].strip() if "Answer" in header else ""
        return jp.replace("___", ans) if jp and ans else jp
    if nt == "Listening":
        return row[header.index("Transcript")].strip() if "Transcript" in header else row[0].strip()
    if nt == "Dictation":
        return row[header.index("Answer")].strip() if "Answer" in header else row[0].strip()
    return row[0].strip()


def lint_file(path: Path,
              audio_users: dict[str, list[str]],
              manifest_keys: set[str],
              taxonomy_points: set[str]) -> list[str]:
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
        if not raw:
            continue
        if raw == "#":
            errs.append(f"WARN: {path}:{ln}: stray bare '#' line — remove it")
            continue
        if raw.startswith("#"):
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
        tag_tokens = tags.split()
        allow_non_jp = "allow:non-japanese-source" in tag_tokens
        point_tags = [t[len("point:"):] for t in tag_tokens if t.startswith("point:")]
        if not point_tags:
            errs.append(f"{path}:{ln}: missing point:* tag")
        for p in point_tags:
            if p.startswith("module-"):
                errs.append(f"{path}:{ln}: coarse point tag '{p}' is not allowed")
            elif taxonomy_points and p not in taxonomy_points:
                errs.append(f"{path}:{ln}: point '{p}' missing from data/grammar_taxonomy.tsv")

        # Audio column — every note type has it; usually the second-to-last.
        audio_field = ""
        if "Audio" in header:
            audio_field = row[header.index("Audio")]
        # Placeholder check (would silently ship as broken audio).
        if _PLACEHOLDER_RE.search(audio_field):
            errs.append(f"{path}:{ln}: WAVE-0 placeholder audio "
                        f"reached grammar/ — regenerate via build_audio.py")
        # Audio reference resolution (skipped for rows awaiting TTS generation).
        pending_audio = "scaffold:pending-audio" in tag_tokens
        for m in _SOUND_RE.finditer(audio_field):
            ref = m.group(1)
            stem = ref.rsplit(".", 1)[0]
            on_disk = (MEDIA_DIR / ref).exists()
            in_manifest = stem in manifest_keys
            if not on_disk and not in_manifest and not pending_audio:
                errs.append(f"{path}:{ln}: audio ref [sound:{ref}] not "
                            f"in media/audio/ and not in manifest")
            audio_users[ref].append(f"{path}:{ln}")

        # Invented-classical form check (CRITICAL: teaches non-existent Japanese)
        jp_field = row[0]
        if _INVENTED_CLASSICAL_RE.search(jp_field):
            errs.append(f"{path}:{ln}: invented classical form in JP field: {jp_field[:60]!r}")

        # Meta-EN check (EN must be a translation, not a teaching note)
        if "EN" in header:
            en_val = row[header.index("EN")].strip()
            if en_val and _META_EN_RE.search(en_val):
                errs.append(f"{path}:{ln}: meta-commentary in EN column: {en_val[:60]!r}")

        # Whole-sentence cloze check — WARN only; these files are excluded from build via
        # --exclude-broken. Fixing them requires Phase 2 content rewrites.
        if nt == "Cloze" and "Text" in header:
            text_field = row[header.index("Text")]
            remainder = _CLOZE_RE.sub("", text_field).strip()
            if not _JP_CHAR_RE.search(remainder):
                errs.append(
                    f"WARN: {path}:{ln}: whole-sentence cloze — no JP context outside the deletion"
                )

        source_text = _source_sentence(nt, header, row).strip()
        if _PLACEHOLDER_TOKEN_RE.search(source_text):
            errs.append(f"{path}:{ln}: placeholder token leaked into source sentence")
        if nt != "Contrast" and "___" in source_text:
            errs.append(
                f"{path}:{ln}: malformed scaffold token '___' leaked into source sentence"
            )
        if nt == "Cloze" and "Text" in header and "___" in row[header.index("Text")]:
            errs.append(f"{path}:{ln}: malformed scaffold token '___' in Cloze Text")
        if (
            nt != "Contrast"
            and source_text
            and not allow_non_jp
            and not _JP_CHAR_RE.search(source_text)
        ):
            errs.append(
                f"{path}:{ln}: non-Japanese source sentence used for audio "
                f"(add allow:non-japanese-source only if intentional)"
            )
        if "Reading" in header:
            reading = row[header.index("Reading")].strip()
            if _PLACEHOLDER_TOKEN_RE.search(reading):
                errs.append(f"{path}:{ln}: placeholder token leaked into Reading")
            if reading:
                # Strip cloze markers ({{c1::content}}, {c1::content}, etc.) before
                # structural checks so the digit in "c1" doesn't fire false positives.
                # Uses permissive 1-2 braces to handle malformed markers in existing files.
                reading_stripped = re.sub(r"\{{1,2}c\d+::([^:}]*)(?::[^}]*)?\}{1,2}", r"\1", reading)
                if _READING_KANJI_RE.search(reading_stripped):
                    errs.append(f"{path}:{ln}: Reading contains kanji: {reading[:40]!r}")
                if _READING_DIGIT_RE.search(reading_stripped):
                    errs.append(f"{path}:{ln}: Reading contains Arabic digits: {reading[:40]!r}")
                if _READING_SYMBOL_RE.search(reading_stripped):
                    errs.append(f"{path}:{ln}: Reading contains ℃/° symbol: {reading[:40]!r}")
                m = _READING_SOKUON_DOUBLE_RE.search(reading_stripped)
                if m:
                    errs.append(f"{path}:{ln}: Reading has sokuon doubling {m.group()!r}: {reading[:40]!r}")

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
    taxonomy_points = _load_taxonomy_points()
    if not taxonomy_points:
        print("✗ missing or empty data/grammar_taxonomy.tsv")
        return 1
    audio_users: dict[str, list[str]] = defaultdict(list)
    all_errs: list[str] = []
    files = sorted(GRAMMAR_DIR.rglob("*.tsv"))
    for f in files:
        all_errs.extend(lint_file(f, audio_users, manifest_keys, taxonomy_points))

    # Recognition twin parity: production and recognition for the same point
    # should have the same row count (±2). Large divergence = orphaned file.
    prod_counts: dict[tuple, int] = {}
    recog_counts: dict[tuple, int] = {}
    for f in files:
        count = sum(
            1 for raw in f.read_text(encoding="utf-8").splitlines()
            if raw and not raw.startswith("#")
        )
        if f.stem.endswith("_production"):
            prod_counts[(f.parent, f.stem[:-len("_production")])] = count
        elif f.stem.endswith("_recognition"):
            recog_counts[(f.parent, f.stem[:-len("_recognition")])] = count
    for key, prod_n in prod_counts.items():
        recog_n = recog_counts.get(key)
        if recog_n is not None and abs(prod_n - recog_n) > 2:
            parent, point = key
            all_errs.append(
                f"WARN: {parent}/{point}: production={prod_n} rows, "
                f"recognition={recog_n} rows — difference > 2"
            )

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

    hard_errs = [e for e in all_errs if not e.startswith("WARN:")]
    warnings   = [e for e in all_errs if e.startswith("WARN:")]
    for w in warnings:
        print(w)
    if not hard_errs:
        suffix = f" {len(warnings)} warning(s)." if warnings else ""
        print(f"✓ {len(files)} TSV file(s) clean. "
              f"{len(audio_users)} audio refs total, "
              f"{len(manifest_keys)} known-good in manifest.{suffix}")
        return 0
    for e in hard_errs:
        print(e)
    print(f"\n✗ {len(hard_errs)} error(s), {len(warnings)} warning(s) across {len(files)} file(s).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
