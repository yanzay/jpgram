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
    import argparse
    import json
    import shutil
    import tempfile

    _ensure_anki()

    parser = argparse.ArgumentParser(description="Build Japanese Grammar Anki package")
    parser.add_argument("--limit", type=int, default=None,
                        help="Limit notes per TSV file (for testing)")
    parser.add_argument("--no-audio", action="store_true",
                        help="Skip media copy")
    parser.add_argument("--out", type=Path, default=OUTPUT,
                        help="Output .apkg path")
    args = parser.parse_args()

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

    # 2. Validate the corpus (optional - continue if it fails due to missing audio files).
    validation_result = _run_hook("validate_anki_data",
                                  [sys.executable, "validate_anki_data.py"])
    if validation_result != 0:
        print(f"  ⚠ Validation had warnings but continuing (audio files may still be missing)")
        # Don't return - continue building despite validation warnings

    print(f"\nBuilding {args.out} (v{VERSION}) from {len(tsvs)} TSV(s)…")
    
    # ── Collection assembly ──
    try:
        from anki.collection import Collection
    except ImportError as e:
        print(f"✗ Failed to import anki modules: {e}")
        return 1

    # Create temporary collection
    tmpdir = Path(tempfile.mkdtemp(prefix="jpgram_"))
    col_path = tmpdir / "collection.anki2"
    
    try:
        col = Collection(str(col_path))
        
        # Create 4 note types
        models = _create_note_types(col)
        
        # Track deck IDs and stats
        deck_ids = {}
        total_notes = 0
        total_cards = 0
        media_files_copied = set()
        
        # Process TSVs
        for tsv_path in tsvs:
            try:
                header, rows = load_tsv(tsv_path)
                if not header or not rows:
                    continue
                
                # Parse headers
                note_type_str = _extract_header(tsv_path, "notetype", "Recognition")
                if note_type_str not in models:
                    print(f"  ⚠ Unknown note type '{note_type_str}' in {tsv_path}, skipping")
                    continue
                
                deck_str = _extract_header(tsv_path, "deck", DECK_NAME)
                if deck_str not in deck_ids:
                    deck_ids[deck_str] = _get_or_create_deck(col, deck_str)
                
                deck_id = deck_ids[deck_str]
                model = models[note_type_str]
                
                # Process rows
                row_count = 0
                for row in rows:
                    if args.limit and row_count >= args.limit:
                        break
                    
                    if not row or len(row) != len(header):
                        continue
                    
                    try:
                        note = col.new_note(model)
                        
                        # Assign field values
                        for i, field_name in enumerate(header):
                            if i < len(row):
                                note[field_name] = row[i]
                        
                        # Parse tags (last column)
                        if len(row) > 0:
                            tags_str = row[-1]
                            if tags_str:
                                note.tags = tags_str.split()
                        
                        col.add_note(note, deck_id)
                        total_notes += 1
                        total_cards += len(note.cards())
                        row_count += 1
                        
                        # Collect media files referenced in this note
                        for field_value in note.values():
                            for match in re.finditer(r'\[sound:([^\]]+\.mp3)\]', field_value):
                                media_files_copied.add(match.group(1))
                    
                    except Exception as e:
                        print(f"  ⚠ Error creating note in {tsv_path}: {e}")
                        continue
                
                if row_count > 0:
                    print(f"  ✓ {tsv_path.name}: {row_count} notes")
            
            except Exception as e:
                print(f"  ✗ Error processing {tsv_path}: {e}")
                continue
        
        # Copy media files
        if not args.no_audio and media_files_copied:
            media_copied = 0
            for fname in media_files_copied:
                src = MEDIA_DIR / "audio" / fname
                if src.exists():
                    dst = Path(col.media.dir()) / fname
                    if not dst.exists():
                        shutil.copy2(src, dst)
                        media_copied += 1
            
            print(f"  ✓ Copied {media_copied} media file(s)")
        
        # Export to .apkg manually (bypass AnkiPackageExporter issues)
        col.close()
        
        # Create .apkg as ZIP with collection.anki2 and media folder
        import zipfile
        
        with zipfile.ZipFile(str(args.out), "w", zipfile.ZIP_DEFLATED) as z:
            # Add collection database
            z.write(str(col_path), "collection.anki2")
            
            # Add collection backup (required by Anki)
            z.write(str(col_path), "collection.anki21")
            
            # Add media manifest - Anki expects numeric string keys -> filename values
            media_dir = Path(col_path.parent) / "collection.media"
            media_json = {}
            media_index = 0
            
            if media_dir.exists() and media_dir.is_dir():
                # Only add files that actually exist
                for fname in sorted(media_dir.iterdir()):
                    if fname.is_file():
                        # Create mapping: "0" -> "filename.mp3", "1" -> "filename2.mp3", etc.
                        # BUT: files in ZIP must be named with the numeric key, not the actual filename!
                        media_json[str(media_index)] = fname.name
                        # Add file to ZIP with numeric name
                        z.write(str(fname), str(media_index))
                        media_index += 1
            
            # Write media JSON (empty dict if no files)
            z.writestr("media", json.dumps(media_json))
        
        # Get file size
        apkg_size = args.out.stat().st_size / (1024 * 1024)  # MB
        
        print(f"\n✓ Built {args.out}")
        print(f"  Notes: {total_notes}")
        print(f"  Cards: {total_cards}")
        print(f"  Media: {len(media_files_copied)}")
        print(f"  Size: {apkg_size:.2f} MB")
        
    except Exception as e:
        print(f"✗ Collection assembly failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # Cleanup tmpdir
        shutil.rmtree(tmpdir, ignore_errors=True)
    
    # 3. Post-build integrity check.
    if Path("validate_apkg.py").exists() and args.out.exists():
        if _run_hook("validate_apkg",
                     [sys.executable, "validate_apkg.py", str(args.out)]) != 0:
            return 4

    return 0


def _extract_header(tsv_path: Path, key: str, default: str) -> str:
    """Extract header value like #deck: or #notetype: from TSV file."""
    lines = tsv_path.read_text(encoding="utf-8").splitlines()
    for line in lines:
        if line.startswith(f"#{key}:"):
            return line[len(f"#{key}:"):].strip()
    return default


def _get_or_create_deck(col, deck_name: str) -> int:
    """Get or create a deck by hierarchical name (e.g. 'A::B::C')."""
    return col.decks.id(deck_name)


def _create_note_types(col):
    """Create 4 note types in collection. Return dict of model_name -> model."""
    models = {}
    
    # Recognition (10 fields)
    models["Recognition"] = _create_note_type(
        col, "Recognition",
        ["JP", "Reading", "EN", "Label", "Formula", "MainUse",
         "QuickCue", "Contrast", "Audio", "Tags"],
        is_cloze=False
    )
    
    # Production (7 fields)
    models["Production"] = _create_note_type(
        col, "Production",
        ["Prompt", "Target", "Reading", "Sample", "Why", "Audio", "Tags"],
        is_cloze=False
    )
    
    # Cloze (5 fields)
    models["Cloze"] = _create_note_type(
        col, "Cloze",
        ["Text", "Reading", "Hint", "Audio", "Tags"],
        is_cloze=True
    )
    
    # Contrast (8 fields)
    models["Contrast"] = _create_note_type(
        col, "Contrast",
        ["JP", "OptionA", "OptionB", "Answer", "Why", "Tip", "Audio", "Tags"],
        is_cloze=False
    )
    
    return models


def _create_note_type(col, name: str, fields: list, is_cloze: bool = False):
    """Create a note type with given fields and template."""
    # Create model
    m = col.models.new(name)
    
    if is_cloze:
        m["type"] = 1  # MODEL_CLOZE = 1
    
    # Add fields
    for field_name in fields:
        col.models.add_field(m, col.models.new_field(field_name))
    
    # Add template(s)
    template = col.models.new_template(name)
    
    if is_cloze:
        # Cloze template
        front_html = "{{cloze:Text}}"
        back_html = "{{cloze:Text}}<hr id=answer>{{Hint}}{{Audio}}"
    else:
        # Load from file or use minimal default
        front_html = _load_template(name, "front")
        back_html = _load_template(name, "back")
    
    template["qfmt"] = front_html
    template["afmt"] = back_html
    
    # Load or create CSS
    css = _load_template(name, "style")
    m["css"] = css
    
    col.models.add_template(m, template)
    col.models.add(m)
    
    return m


def _load_template(note_type: str, part: str) -> str:
    """Load template from file or return minimal default."""
    ext = "css" if part == "style" else "html"
    template_path = Path("templates") / f"{note_type}.{part}.{ext}"
    
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    
    # Minimal defaults - show FrontSide for all
    if part == "front":
        return "<div style='font-size:1.2em;'>{{#JP}}{{JP}}<br>{{/JP}}{{#Prompt}}{{Prompt}}<br>{{/Prompt}}{{#Text}}{{Text}}<br>{{/Text}}</div>"
    elif part == "back":
        return "<div>{{FrontSide}}<hr id=answer><div style='font-size:1em;'>{{#EN}}EN: {{EN}}<br>{{/EN}}{{#Target}}Target: {{Target}}<br>{{/Target}}{{#Reading}}Reading: {{Reading}}<br>{{/Reading}}{{#OptionA}}A: {{OptionA}}<br>{{/OptionA}}{{#OptionB}}B: {{OptionB}}<br>{{/OptionB}}{{#Answer}}Answer: {{Answer}}<br>{{/Answer}}{{#Why}}{{Why}}<br>{{/Why}}{{#Hint}}{{Hint}}<br>{{/Hint}}{{#Audio}}{{Audio}}<br>{{/Audio}}</div></div>"
    else:  # style
        return ".card { font-family: Arial; font-size: 20px; color: #000; background: #fff; } hr { border: 1px solid #ccc; } #answer { margin: 1em 0; }"


if __name__ == "__main__":
    sys.exit(main())
