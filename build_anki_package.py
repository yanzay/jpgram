#!/usr/bin/env python3
"""
Build script for the Japanese Grammar Anki package.

Produces: japanese_grammar_anki.apkg

Reads every TSV under ./grammar/ and assembles a hierarchical deck:

  Japanese Grammar
    00 - Foundation (Kana + Particles)
    01 - N5 Grammar
        :: Recognition / Production / Cloze / Contrast
    02 - N4 Grammar
        :: Recognition / Production / Cloze / Contrast
    03 - N3 Grammar
        :: Recognition / Production / Cloze / Contrast
    04 - N2 Grammar
        :: Recognition / Production / Cloze / Contrast
    05 - N1 Grammar
        :: Recognition / Production / Cloze / Contrast
    06 - Keigo (Honorifics)
    07 - Casual / Spoken Forms
    08 - Slang & Internet Speech
    09 - Sentence-Final Particles & Aizuchi
    10 - Onomatopoeia (擬音語・擬態語)
    11 - Classical / Literary Carryover
    12 - Beyond N1 (Idioms, Set Phrases, 四字熟語)
    13 - L1 Interference (per-language contrasts)

This is a SKELETON. The note types and packaging logic are defined here
but actual TSV content is generated incrementally per-wave per
CONTENT_PLAN.md.
"""

import csv
import hashlib
import json
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
# Mirrors the schema in `verbs/` but JP-specific. Each TSV under grammar/
# declares its `#columns:` header which MUST match the corresponding
# fields list below.

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


def load_tsv(path):
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    header = None
    data_lines = []
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
    """Heuristic: filename like '*_recognition.tsv' / '*_cloze.tsv' …"""
    name = tsv_path.stem.lower()
    if "recognition" in name: return "Recognition"
    if "production"  in name: return "Production"
    if "cloze"       in name: return "Cloze"
    if "contrast"    in name: return "Contrast"
    return "Recognition"


def main():
    _ensure_anki()
    if not GRAMMAR_DIR.exists():
        print(f"No grammar/ directory yet (skeleton-only build). "
              f"See CONTENT_PLAN.md.")
        return

    tsvs = sorted(GRAMMAR_DIR.rglob("*.tsv"))
    if not tsvs:
        print("grammar/ exists but contains no TSVs yet. "
              "Generate content per CONTENT_PLAN.md, then re-run.")
        return

    print(f"Building {OUTPUT} (v{VERSION}) from {len(tsvs)} TSV(s)…")
    # NOTE: actual collection assembly is intentionally elided in the
    # skeleton commit. The real implementation follows the same recipe
    # used by ../verbs/build_anki_package.py (Collection → add_model →
    # add_note loop → export to .apkg with media manifest). We add it in
    # wave 1 once we have any content to package.
    print("  (skeleton: note types declared, content waves still pending)")
    print(f"  Note types: {list(NOTE_TYPES)}")
    print(f"  Deck name:  {DECK_NAME}")


if __name__ == "__main__":
    main()
