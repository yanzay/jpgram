#!/usr/bin/env python3
"""
Build script for the Japanese Grammar Anki package.

Produces: japanese_grammar_anki.apkg

Reads every TSV under ./grammar/ and assembles a hierarchical deck:

  Japanese Grammar
    00 - Foundation (Kana + Particles + Pitch Accent)
    01 - N5 Grammar         :: Recognition / Production / Cloze / Contrast
    02 - N4 Grammar
    03 - N3 Grammar
    04 - N2 Grammar
    05 - N1 Grammar
    06 - Keigo (Honorifics)
    07 - Casual / Spoken Forms
    08 - Slang & Internet Speech
    09 - Sentence-Final Particles & Aizuchi
    10 - Onomatopoeia
    11 - Classical / Literary Carryover
    12 - Beyond N1 (Idioms, Set Phrases, 四字熟語)
    13 - L1 Interference (per-language)

Build flow:
    apply_taxonomy_tags  →  validate_anki_data  →  Collection assembly
    →  export .apkg  →  validate_apkg

The Collection-assembly step (~700 LOC) is intentionally elided in the
Wave-0 commit — it follows the same recipe as ../verbs/build_anki_package.py
and lands in Wave 1 alongside the first real content. The skeleton already
fails loudly (sys.exit non-zero) when something is wrong.
"""

import csv
import os
import re
import subprocess
import sys
from pathlib import Path

VERSION = "0.1.0"
DECK_NAME = "Japanese Grammar"
GRAMMAR_DIR = Path("grammar")
MEDIA_DIR = Path("media")
OUTPUT = Path("japanese_grammar_anki.apkg")
CHANGELOG_URL = "https://github.com/yanzay/jpgram/blob/main/CHANGELOG.md"


# ── Note-type schema ─────────────────────────────────────────────────────
# Every TSV's `#columns:` directive must match the field list for its
# note type, in this order. The validator enforces this.
NOTE_TYPES = {
    "Recognition": [
        "JP", "Reading", "EN", "Label", "Formula", "MainUse",
        "QuickCue", "Contrast", "Audio", "Tags",
    ],
    "Production": [
        "Prompt", "Target", "Reading", "Sample", "Why", "Audio", "Tags",
    ],
    "Cloze": [
        "Text", "Reading", "Hint", "Audio", "Tags",
    ],
    "Contrast": [
        "JP", "OptionA", "OptionB", "Answer", "Why", "Tip",
        "Audio", "Tags",
    ],
}


def _ensure_anki():
    try:
        import anki  # noqa: F401
        return
    except ImportError:
        pass
    print("  [setup] official `anki` package not found; installing…")
    subprocess.check_call([sys.executable, "-m", "pip", "install",
                           "--user", "--break-system-packages", "anki>=24.0"])


def load_tsv(path: Path):
    lines = path.read_text(encoding="utf-8").splitlines()
    header = None
    data_lines: list[str] = []
    for line in lines:
        if line.startswith("#columns:"):
            header = line[len("#columns:"):].split("\t")
            continue
        if not line or line.startswith("#"):
            continue
        data_lines.append(line)
    reader = csv.reader(data_lines, delimiter="\t", quotechar='"')
    return header, [row for row in reader if row]


def detect_note_type(tsv_path: Path) -> str:
    """Filename like `<point>_recognition.tsv` → 'Recognition'."""
    name = tsv_path.stem.lower()
    if "recognition" in name: return "Recognition"
    if "production"  in name: return "Production"
    if "cloze"       in name: return "Cloze"
    if "contrast"    in name: return "Contrast"
    return "Recognition"


# ── Pre-build hooks ──────────────────────────────────────────────────────
def _run_hook(label: str, argv: list[str]) -> int:
    print(f"\n→ {label}: {' '.join(argv)}")
    rc = subprocess.call(argv)
    if rc != 0:
        print(f"  ✗ {label} failed (rc={rc})")
    return rc


def main() -> int:
    _ensure_anki()

    if not GRAMMAR_DIR.exists():
        print(f"grammar/ does not exist (skeleton-only build).")
        return 1

    tsvs = sorted(GRAMMAR_DIR.rglob("*.tsv"))
    if not tsvs:
        print("grammar/ has no TSVs yet. See CONTENT_PLAN.md for the wave plan.")
        return 1

    # 1. Inject taxonomy tags (idempotent).
    if Path("apply_taxonomy_tags.py").exists():
        if _run_hook("apply_taxonomy_tags",
                     [sys.executable, "apply_taxonomy_tags.py"]) != 0:
            return 2

    # 2. Validate the corpus.
    if _run_hook("validate_anki_data",
                 [sys.executable, "validate_anki_data.py"]) != 0:
        return 3

    print(f"\nBuilding {OUTPUT} (v{VERSION}) from {len(tsvs)} TSV(s)…")
    # ── Collection assembly: TODO Wave 1.
    # The full implementation follows ../verbs/build_anki_package.py:
    #   Collection() → add_model per NOTE_TYPES → add_deck per JLPT level
    #   → add_note loop → media manifest copy → export to .apkg.
    print("  (skeleton: Collection assembly lands in Wave 1)")
    print(f"  Note types: {list(NOTE_TYPES)}")
    print(f"  Deck name:  {DECK_NAME}")

    # 3. Post-build integrity check.
    if Path("validate_apkg.py").exists() and OUTPUT.exists():
        if _run_hook("validate_apkg",
                     [sys.executable, "validate_apkg.py", str(OUTPUT)]) != 0:
            return 4

    return 0


if __name__ == "__main__":
    sys.exit(main())
