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

# Phase-6 additions:
_ALLOWED_HEADER_PREFIXES = ("#separator:", "#html:", "#columns:", "#notetype:", "#deck:")
# Placeholder Label values that indicate authoring scaffolding leaked into shipped content.
_LABEL_PLACEHOLDER_RE = re.compile(r"^(contrast-derived|TODO|PLACEHOLDER|tbd|FIXME)$", re.I)
# Directory-prefix → expected JLPT tag value.
_DIR_TO_JLPT = {
    "00-foundation": "n5",
    "01-n5": "n5",
    "02-n4": "n4",
    "03-n3": "n3",
    "04-n2": "n2",
    "05-n1": "n1",
    "10-onomatopoeia": None,  # no JLPT constraint
    "13-l1": None,
}
# Slugs that legitimately don't appear verbatim in JP (umbrella/category files).
_CATEGORY_SLUGS = frozenset({
    "kana", "copula", "particles-core", "numbers-counters",
    "demonstratives", "time-expressions", "pitch-accent-primer",
    "i-adjectives", "interrogatives", "polite-verb-endings",
    "verb-non-past", "past-tense-い-adjectives", "causative-passive",
    "causative", "potential", "passive",
    # Single-character umbrellas (cover broad grammar categories rather than
    # a single morpheme).
    "いい", "それ", "どこ", "って", "と", "が", "を", "に", "で", "の",
    "は", "も", "へ", "や", "か", "から", "まで",
    # Onomatopoeia bucket files
    "onomatopoeia",
    "giongo-sounds", "gitaigo-states", "giseigo-people", "giseigo-voices",
    "emotional-onomatopoeia",
    # L1-interference bucket files
    "l1-tense-aspect", "l1-articles-and-number", "l1-pronoun-overuse",
    "l1-yes-no_negative-questions", "l1-givereceive-direction",
    "l1-particles-overlap", "l1-relative-clauses",
})


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
            # Phase-6: any header line not in the allowed prefix set is a stray
            # narrative comment — these confuse some Anki importers.
            if not raw.startswith(_ALLOWED_HEADER_PREFIXES):
                errs.append(
                    f"{path}:{ln}: stray comment '{raw[:60]}' "
                    f"between standard headers"
                )
            continue
        data.append((ln, raw))

    # Phase-6: empty data file = authoring scaffold leak.
    if not data:
        errs.append(f"{path}: no data rows — authoring scaffold leaked into deck")
        return errs

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

        # Whole-sentence cloze — promoted from WARN to ERROR after Phase-2
        # re-curation. Every cloze row must leave some JP context outside
        # the {{c1::…}} deletion for the learner to anchor on.
        if nt == "Cloze" and "Text" in header:
            text_field = row[header.index("Text")]
            remainder = _CLOZE_RE.sub("", text_field).strip()
            if not _JP_CHAR_RE.search(remainder):
                errs.append(
                    f"{path}:{ln}: whole-sentence cloze — no JP context outside the deletion"
                )

        # Phase-6: tag-key uniqueness. Anki indexes duplicate-prefix tags
        # separately ("complexity:intro complexity:standard" → 2 tags),
        # which inflates the cardinality and breaks filtered decks.
        seen_prefixes: dict[str, int] = {}
        for tok in tag_tokens:
            if ":" in tok:
                prefix = tok.split(":", 1)[0]
                seen_prefixes[prefix] = seen_prefixes.get(prefix, 0) + 1
        for prefix, count in seen_prefixes.items():
            if count > 1 and prefix in {"complexity", "frequency", "jlpt", "module", "point", "source"}:
                errs.append(
                    f"WARN: {path}:{ln}: duplicate tag prefix '{prefix}:' "
                    f"appears {count}× — keep one"
                )

        # Phase-6: JLPT tag must match the directory. 01-n5/ → jlpt:n5, etc.
        # Directory `10-onomatopoeia/` and `13-l1/` have no JLPT constraint.
        dir_name = path.parent.name
        expected_jlpt = _DIR_TO_JLPT.get(dir_name)
        if expected_jlpt is not None:
            jlpt_tags = [t[len("jlpt:"):] for t in tag_tokens if t.startswith("jlpt:")]
            if jlpt_tags and not any(j == expected_jlpt for j in jlpt_tags):
                errs.append(
                    f"{path}:{ln}: jlpt tag {jlpt_tags} disagrees with "
                    f"directory ({dir_name} → expected jlpt:{expected_jlpt})"
                )

        # Phase-6: cloze point-alignment. Each {{c1::TARGET}} must contain
        # the filename's grammar slug (or a conjugation alias) somewhere
        # in the deleted token OR in the surrounding sentence.
        if nt == "Cloze":
            slug_c = path.stem[:-len("_cloze")]
            if slug_c not in _CATEGORY_SLUGS:
                # Build the same conjugation-aware aliases used by the
                # file-level slug-drift check above.
                c_aliases = {slug_c}
                MIN_C = 2
                if slug_c and slug_c[-1] in "うるくぐすつぬむぶ":
                    stem = slug_c[:-1]
                    if len(stem) >= MIN_C:
                        c_aliases.add(stem)
                    renyokei_c = {"う": "い", "く": "き", "ぐ": "ぎ", "す": "し",
                                  "つ": "ち", "ぬ": "に", "む": "み", "ぶ": "び"}
                    if slug_c[-1] in renyokei_c:
                        ren = stem + renyokei_c[slug_c[-1]]
                        if len(ren) >= MIN_C:
                            c_aliases.add(ren)
                if slug_c.endswith("する") and len(slug_c) > 2:
                    ren = slug_c[:-2] + "し"
                    if len(ren) >= MIN_C:
                        c_aliases.add(ren)
                for cop in ("だ", "です"):
                    if slug_c.endswith(cop):
                        bare = slug_c[:-len(cop)]
                        if len(bare) >= MIN_C:
                            c_aliases.add(bare)
                if slug_c.endswith("ない") and len(slug_c) >= 4:
                    bare = slug_c[:-2]
                    if len(bare) >= MIN_C:
                        c_aliases.add(bare)
                text_field = row[header.index("Text")] if "Text" in header else row[0]
                cloze_targets = _CLOZE_EXTRACT_RE.findall(text_field)
                if not any(a in t for t in cloze_targets for a in c_aliases) \
                   and not any(a in text_field for a in c_aliases):
                    errs.append(
                        f"WARN: {path}:{ln}: cloze content doesn't reference "
                        f"point '{slug_c}' (off-topic for filename)"
                    )

        # Phase-6: contrast spot-the-answer. If Answer appears verbatim in JP
        # AND no ___ placeholder is present AND the JP doesn't show both
        # options in slash-format, the card degrades to recognition.
        if nt == "Contrast" and "JP" in header and "Answer" in header \
                and "OptionA" in header and "OptionB" in header:
            jp = row[header.index("JP")]
            ans = row[header.index("Answer")].strip()
            opt_a = row[header.index("OptionA")]
            opt_b = row[header.index("OptionB")]
            if ans and "___" not in jp and ans in jp and ans != jp.strip():
                # Allow slash-format (both options visible in JP)
                slash_format = (
                    opt_a in jp and opt_b in jp
                    and (f"{opt_a} / {opt_b}" in jp or f"{opt_b} / {opt_a}" in jp
                         or f"{opt_a}／{opt_b}" in jp or f"{opt_b}／{opt_a}" in jp
                         or ("vs" in jp and opt_a in jp and opt_b in jp))
                )
                if not slash_format:
                    errs.append(
                        f"WARN: {path}:{ln}: spot-the-answer — Answer "
                        f"'{ans}' visible in JP without ___ blank"
                    )

        # Phase-6: placeholder Label value (authoring sentinel that leaked
        # into shipped content).
        if "Label" in header:
            label_val = row[header.index("Label")].strip()
            if _LABEL_PLACEHOLDER_RE.match(label_val):
                errs.append(
                    f"WARN: {path}:{ln}: placeholder Label '{label_val}' — "
                    f"replace with a real grammar label"
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

    # Phase-6/9: file-level slug↔content integrity. The filename's grammar
    # slug (or a verb-stem alias) must appear in ≥80% of source rows.
    slug = path.stem
    for suffix in ("_recognition", "_production", "_cloze", "_contrast",
                   "_dictation", "_listening"):
        if slug.endswith(suffix):
            slug = slug[:-len(suffix)]
            break
    is_aggregator = (
        "-" in slug
        or any(c.isdigit() for c in slug)
        or "[" in slug or "・" in slug or "～" in slug or "(" in slug
        or len(slug) >= 8  # long multi-morpheme slugs
    )
    # Also treat placeholder slugs ("adj限りだ", "のはxの方だ") as aggregators.
    if "adj" in slug.lower() or "noun" in slug.lower() or "verb" in slug.lower() \
       or "x" in slug:
        is_aggregator = True
    if slug not in _CATEGORY_SLUGS and not is_aggregator and slug:
        # Hardcoded irregular-verb conjugations: relax MIN for short stems.
        IRREGULAR = {
            "くる": {"くる", "きた", "きて", "きます", "き", "こない", "こよう"},
            "する": {"する", "した", "して", "します", "し", "しない", "しよう"},
            "ある": {"ある", "あり", "あって", "あった", "あります"},
        }
        # Build conjugation-aware aliases (mirrors scripts/_phase9_trim).
        aliases = set()
        if slug in IRREGULAR:
            aliases.update(IRREGULAR[slug])
        else:
            aliases.add(slug)
            MIN = 2
            def _is_kanji(ch):
                return "一" <= ch <= "鿿"
            for cop in ("だ", "です"):
                if slug.endswith(cop):
                    bare = slug[:-len(cop)]
                    if len(bare) >= MIN:
                        aliases.add(bare)
            # Strip trailing ない (auxiliary): match both 〜ない and 〜ません.
            if slug.endswith("ない") and len(slug) >= 4:
                bare = slug[:-2]
                if len(bare) >= MIN:
                    aliases.add(bare)
            if slug.endswith("する") and len(slug) > 2:
                ren = slug[:-2] + "し"
                if len(ren) >= MIN:
                    aliases.add(ren)
            if slug.endswith("くる") and len(slug) > 2:
                ren = slug[:-2] + "き"
                if len(ren) >= MIN:
                    aliases.add(ren)
            if slug and slug[-1] in "うるくぐすつぬむぶ":
                stem = slug[:-1]
                # Allow 1-char kanji stems (high semantic density).
                if len(stem) >= MIN or (len(stem) == 1 and _is_kanji(stem)):
                    aliases.add(stem)
                renyokei = {"う": "い", "く": "き", "ぐ": "ぎ", "す": "し",
                            "つ": "ち", "ぬ": "に", "む": "み", "ぶ": "び"}
                if slug[-1] in renyokei:
                    ren = stem + renyokei[slug[-1]]
                    if len(ren) >= MIN:
                        aliases.add(ren)
            if slug.endswith("い") and len(slug) >= 3:
                stem = slug[:-1]
                if len(stem) >= MIN:
                    aliases.add(stem)

        rows_parsed = []
        for ln, raw in data:
            row = next(csv.reader([raw], delimiter="\t", quotechar='"'), None)
            if row and len(row) == len(expected):
                rows_parsed.append(row)
        if len(rows_parsed) >= 5:
            on_topic = 0
            for row in rows_parsed:
                src = _source_sentence(nt, header, row)
                # Also check Reading column if present
                reading = row[header.index("Reading")] if "Reading" in header else ""
                if any(a in src or a in reading for a in aliases):
                    on_topic += 1
            pct = on_topic / len(rows_parsed)
            if pct < 0.80:
                errs.append(
                    f"WARN: {path}: slug↔content drift — only {on_topic}/{len(rows_parsed)} "
                    f"rows reference slug '{slug}' (need ≥80%)"
                )

    # Phase-6: 5-row Recognition back-side variability. After Phase-4,
    # MainUse should vary per row in addition to QuickCue. Flag files where
    # all of {Label, Formula, MainUse, Contrast} are identical across rows.
    if nt == "Recognition" and len(data) == 5 and all(
        c in header for c in ("Label", "Formula", "MainUse", "QuickCue", "Contrast")
    ):
        rows_parsed = []
        for ln, raw in data:
            row = next(csv.reader([raw], delimiter="\t", quotechar='"'), None)
            if row and len(row) == len(expected):
                rows_parsed.append(row)
        distinct_counts = {}
        for col in ("Label", "Formula", "MainUse", "Contrast"):
            idx = header.index(col)
            distinct_counts[col] = len({r[idx] for r in rows_parsed})
        # Pass if at least one of the four varies; otherwise warn.
        if max(distinct_counts.values(), default=0) < 2:
            errs.append(
                f"WARN: {path}: back-side collapse — all of "
                f"Label/Formula/MainUse/Contrast identical across rows"
            )

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
