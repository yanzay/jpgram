#!/usr/bin/env python3
"""
Content-quality gate for grammar-strict/ TSVs.

Checks that block merges (exit 1 on any violation):
  - empty-reading        : recognition/production row has Japanese but no hiragana Reading
  - sentence-end         : JP/Sample ≥ 20 chars with no terminal 。！？」』）…
  - ascii-question-mark  : '?' in JP/Sample instead of '？'
  - label-suffix         : JP/Sample ends with a '〜…' label tag appended after the sentence
  - column-count         : row has wrong number of tab-separated fields
  - bogus-audio-in-field : [sound:…] ref in a non-Audio column (QuickCue, Contrast, etc.)
  - missing-audio-file   : [sound:HASH.mp3] in Audio col but file not on disk

Checks that warn only (exit 0, printed for awareness):
  - vague-formula        : Formula is a short English-only word for N4-N1 grammar files
  - label-contamination  : dominant Label in recognition file doesn't match the slug
                           (after excluding known collection files)

Usage:
  python3 validate_content_quality.py [--strict]   # --strict makes warnings blocking
"""
from __future__ import annotations
import argparse, re, sys
from collections import defaultdict
from pathlib import Path

GRAMMAR_DIR  = Path("grammar-strict")
AUDIO_DIR    = Path("media/audio")

# ── Collection files: multi-point thematic groups (label != slug is expected) ──
COLLECTION_SLUGS = {
    "copula", "particles-core", "demonstratives", "numbers-counters",
    "time-expressions", "kana", "pitch-accent-primer", "pitch-accent",
}

# ── File categories exempt from formula check ────────────────────────────────
FORMULA_EXEMPT_DIRS = {"00-foundation", "10-onomatopoeia"}

STRUCTURAL_RE = re.compile(
    r'\b(V|N|Adj|Noun|verb|stem|dict|plain|masu|て|た|ない|の|に|が|を|で'
    r'|する|なる|ある|く|い|な|volitional|passive|causative|conditional)\b',
    re.IGNORECASE
)
JP_RE       = re.compile(r'[一-龯ぁ-んァ-ン]')
END_RE      = re.compile(r'[。！？」』）…]$')
LABEL_SUF   = re.compile(r'\s*〜\S+$')
SOUND_COL   = re.compile(r'\[sound:[a-f0-9]{12}\.mp3\]')


def get_col(parts: list[str], cols: list[str], name: str, fallback: int = -1) -> str:
    idx = cols.index(name) if name in cols else fallback
    return parts[idx].strip() if 0 <= idx < len(parts) else ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true",
                    help="Treat warnings as errors")
    args = ap.parse_args()

    if not GRAMMAR_DIR.exists():
        print(f"ERROR: {GRAMMAR_DIR} not found", file=sys.stderr)
        return 1

    audio_on_disk: set[str] = set()
    if AUDIO_DIR.exists():
        audio_on_disk = {f.name for f in AUDIO_DIR.glob("*.mp3")}

    errors: list[str]   = []
    warnings: list[str] = []
    total_rows = 0

    for tsv in sorted(GRAMMAR_DIR.rglob("*.tsv")):
        stem = tsv.stem.lower()
        is_rec      = stem.endswith("_recognition")
        is_prod     = stem.endswith("_production")
        is_cloze    = stem.endswith("_cloze")
        is_contrast = stem.endswith("_contrast")
        is_listen   = stem.endswith("_listening")
        is_dict     = stem.endswith("_dictation")

        if not any([is_rec, is_prod, is_cloze, is_contrast, is_listen, is_dict]):
            continue

        raw  = tsv.read_text(encoding="utf-8")
        lines = raw.splitlines()
        cols_line = next((l[len("#columns:"):] for l in lines
                          if l.startswith("#columns:")), "")
        cols = cols_line.split("\t") if cols_line else []
        expected_cols = len(cols)
        slug = tsv.stem.rsplit("_", 1)[0]
        level_dir = tsv.parent.name

        jp_idx = (
            cols.index("Sample") if is_prod and "Sample" in cols else
            cols.index("JP")     if "JP"     in cols else 0
        )
        audio_idx   = cols.index("Audio")   if "Audio"   in cols else -1
        reading_idx = cols.index("Reading") if "Reading" in cols else -1
        label_idx   = cols.index("Label")   if "Label"   in cols else -1
        formula_idx = cols.index("Formula") if "Formula" in cols else -1
        tags_idx    = cols.index("Tags")    if "Tags"    in cols else -1

        # ── Per-file label-contamination (recognition, non-collection) ────────
        if is_rec and label_idx >= 0 and slug not in COLLECTION_SLUGS:
            slug_n = re.sub(r"[〜ー～\-\s]", "", slug.lower())
            data_rows = [l for l in lines if not l.startswith("#") and l.strip()]
            if data_rows and len(slug_n) > 2:
                all_labels = [r.split("\t")[label_idx].strip()
                              for r in data_rows
                              if len(r.split("\t")) > label_idx]
                if all_labels:
                    from collections import Counter
                    match = sum(1 for lb in all_labels
                                if slug_n in re.sub(r"[〜ー～\-\s]", "", lb.lower()))
                    pct = (match / len(all_labels)) * 100
                    if pct < 50:
                        top = Counter(all_labels).most_common(1)[0][0]
                        warnings.append(
                            f"[label-contamination] {tsv.parent.name}/{tsv.name}: "
                            f"{pct:.0f}% of labels match slug '{slug}'; "
                            f"dominant label is '{top}'"
                        )

        # ── Per-row checks ────────────────────────────────────────────────────
        for lineno, line in enumerate(lines, 1):
            if line.startswith("#") or not line.strip():
                continue
            total_rows += 1
            parts = line.split("\t")
            loc = f"{tsv.parent.name}/{tsv.name}:{lineno}"

            # Column count
            if expected_cols and len(parts) != expected_cols:
                errors.append(
                    f"[column-count] {loc}: {len(parts)} fields, expected {expected_cols}"
                )

            # Bogus audio ref in non-Audio columns
            for ci, part in enumerate(parts):
                if ci == audio_idx:
                    continue
                col_name = cols[ci] if ci < len(cols) else f"col{ci}"
                if SOUND_COL.search(part):
                    errors.append(
                        f"[bogus-audio-in-field] {loc}: [sound:…] in '{col_name}' column"
                    )

            # Skip listening/dictation for content checks
            if is_listen or is_dict:
                continue

            jp = parts[jp_idx].strip() if jp_idx < len(parts) else ""
            if not jp:
                continue

            # Missing-audio-file (skip rows tagged scaffold:pending-audio)
            tags_val = parts[tags_idx].strip() if tags_idx >= 0 and tags_idx < len(parts) else ""
            pending_audio = "scaffold:pending-audio" in tags_val.split()
            if audio_idx >= 0 and audio_idx < len(parts) and not pending_audio:
                audio_val = parts[audio_idx].strip()
                m = re.search(r"\[sound:([a-f0-9]{12}\.mp3)\]", audio_val)
                if m and m.group(1) not in audio_on_disk:
                    errors.append(
                        f"[missing-audio-file] {loc}: {m.group(1)} not on disk"
                    )

            if not JP_RE.search(jp):
                continue  # Skip non-Japanese rows (e.g. English contrast patterns)

            # Empty reading
            if (is_rec or is_prod) and reading_idx >= 0:
                reading = parts[reading_idx].strip() if reading_idx < len(parts) else ""
                if not reading:
                    errors.append(f"[empty-reading] {loc}: JP has kanji but Reading is empty")

            # Sentence-end punctuation (≥ 20 chars)
            if (is_rec or is_prod) and len(jp) >= 20:
                if not END_RE.search(jp):
                    errors.append(
                        f"[sentence-end] {loc}: no terminal punctuation — {jp[:55]!r}"
                    )
                if "?" in jp:
                    errors.append(
                        f"[ascii-question-mark] {loc}: use '？' not '?' — {jp[:55]!r}"
                    )

            # Label suffix
            if (is_rec or is_prod) and LABEL_SUF.search(jp):
                errors.append(
                    f"[label-suffix] {loc}: trailing 〜… label in JP field — {jp[:55]!r}"
                )

            # Vague formula (recognition, grammar files only)
            if is_rec and formula_idx >= 0 and level_dir not in FORMULA_EXEMPT_DIRS:
                formula = parts[formula_idx].strip() if formula_idx < len(parts) else ""
                if (formula
                        and not STRUCTURAL_RE.search(formula)
                        and len(formula) < 25
                        and not any(c in formula for c in "〜・・+→←")):
                    warnings.append(
                        f"[vague-formula] {loc}: Formula={formula!r} — "
                        "add morphological pattern (e.g. 'V-plain + そうだ')"
                    )

    # ── Report ────────────────────────────────────────────────────────────────
    print(f"Checked {total_rows} rows across {GRAMMAR_DIR}")
    print()

    if errors:
        print(f"ERRORS ({len(errors)}):")
        for e in errors:
            print(f"  {e}")
        print()

    if warnings:
        print(f"WARNINGS ({len(warnings)}):")
        for w in warnings[:40]:
            print(f"  {w}")
        if len(warnings) > 40:
            print(f"  ... and {len(warnings) - 40} more")
        print()

    blocking = errors + (warnings if args.strict else [])
    if blocking:
        print(f"✗ {len(errors)} error(s), {len(warnings)} warning(s). "
              f"{'All blocking (--strict).' if args.strict else 'Errors are blocking.'}")
        return 1

    print(f"✓ {len(errors)} errors, {len(warnings)} warnings.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
