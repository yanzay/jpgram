# Japanese Grammar Anki Package

A Bunpro-atomic Japanese-grammar Anki deck covering all 945 Bunpro grammar
points from N5 through N1, with two primary card types per point:
**Recognition** and **Production**, plus secondary Cloze / Contrast /
Dictation / Listening cards on a subset of points.

## Coverage

| Level | Points | Directory |
|-------|--------|-----------|
| Foundation | — | `grammar-strict/00-foundation/` |
| N5 | 122 | `grammar-strict/01-n5/` |
| N4 | 160 | `grammar-strict/02-n4/` |
| N3 | 194 | `grammar-strict/03-n3/` |
| N2 | 203 | `grammar-strict/04-n2/` |
| N1 | 169 | `grammar-strict/05-n1/` |
| **Total** | **945** | |

Foundation cards (kana, particles, copula, numbers, time, demonstratives)
live in `grammar-strict/00-foundation/`.

## Card types

| Note type | Front | Back |
|-----------|-------|------|
| **Recognition** | JP sentence + 🔊 | label · formula · main use · quick cue · contrast |
| **Production** | English prompt + target form | model JP + reading + why + 🔊 |
| **Cloze** | sentence with `{{c1::…}}` blank + hint | full sentence + reading + 🔊 |
| **Contrast** | JP with `___` + option A / B + 🔊 | correct answer highlighted + why + tip |
| **Dictation** | 🔊 only | transcript + reading |
| **Listening** | 🔊 only | transcript + meaning |

### Fields

| Note type | Fields |
|-----------|--------|
| Recognition | `JP · Reading · EN · Label · Formula · MainUse · QuickCue · Contrast · Audio · Tags` |
| Production | `Prompt · Target · Reading · Sample · Why · Audio · Tags` |
| Cloze | `Text · Reading · Hint · Audio · Tags` |
| Contrast | `JP · OptionA · OptionB · Answer · Why · Tip · Audio · Tags` |

## Repository layout

```
grammar-strict/         One TSV per grammar point per card type
  00-foundation/
  01-n5/ … 05-n1/

content/                Python source for authored sentences
  n5_strict_content.py
  n4_strict_content.py
  n3_strict_content_merged.py
  n2_strict_content_merged.py
  n1_strict_content_merged.py

scripts/
  generate_strict_content.py   Reads content/*.py → writes grammar-strict/ TSVs
  jp_reading.py                fugashi + UniDic hiragana reading generator
  strict_deck_audit.py         Runs coverage_audit + bunpro_reverse_coverage
  coverage_audit.py            Internal + Bunpro coverage gates
  bunpro_reverse_coverage.py   Verifies all 945 Bunpro points covered

templates/              HTML + CSS card templates for all note types
draft/                  Schema-only example TSVs (not picked up by build)

data/
  grammar_taxonomy_bunpro.tsv  Bunpro slug → point metadata
  grammar_taxonomy.tsv         Full cross-reference taxonomy
  grammar-refs/                Cached Bunpro/Tofugu/Imabi index files
  dictionaries/                UniDic, JMDict, MeCab dictionaries
  frequency-lists/             BCCWJ-derived frequency rankings
  pitch-accent/                NHK pitch accent dictionary

build_anki_package.py   Assembles grammar-strict/ → japanese_grammar_anki.apkg
build_audio.py          Google Cloud TTS: one MP3 per unique JP sentence (idempotent)
build_furigana.py       Injects <ruby> furigana into Reading fields
build_pitchaccent.py    Injects pitch-accent overlays
validate_anki_data.py   Validates all TSVs (12+ quality rules)
apply_taxonomy_tags.py  Injects register/frequency/domain/JLPT tags
```

## Quick start

```bash
# 1. Install deps
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Verify deck integrity
.venv/bin/python scripts/strict_deck_audit.py
# Expected: strict_deck_audit: exit=0  bunpro_reverse_coverage: pct=100.0% covered=945/945

# 3. Build Anki package
python build_anki_package.py

# 4. Generate audio — requires GCP credentials
# Drop service-account JSON at .secrets/gcp-adc.json or use:
#   gcloud auth application-default login
python build_audio.py --dry-run    # cost preview
python build_audio.py              # synthesize all sentences
```

## Adding / updating content

Content lives in `content/<level>_strict_content.py` as a Python `CONTENT` dict.
Each entry has `label`, `formula`, `main_use`, `contrast`, and `sentences`
(target: 5 atomic sentences per point, each with `jp`, `en`, `why` ≤ 8 words).

After editing a content file, regenerate TSVs:

```bash
.venv/bin/python scripts/generate_strict_content.py \
    --content content/<level>_strict_content.py \
    --module <module>    # e.g. 01-n5, 02-n4, …, 05-n1
```

To author a new TSV from scratch, copy the matching schema example from
`draft/` into `grammar-strict/<module>/`, rename it
`<point-slug>_<notetype>.tsv`, fill in real rows, then:

```bash
python apply_taxonomy_tags.py
python validate_anki_data.py
```

### Validator rules

`validate_anki_data.py` enforces hard errors on:
- Empty data files (no rows)
- Whole-sentence cloze (entire JP wrapped in `{{c1::…}}`)
- Cloze point-alignment (≥80% of cloze deletions must match the filename slug)
- Contrast spot-the-answer (answer literal in JP with no `___` placeholder)
- Tag-key uniqueness per row (no duplicate `jlpt:`, `complexity:`, etc.)
- JLPT-tag-vs-directory consistency
- Placeholder leak (`Label="contrast-derived"` or `TODO` in non-tag fields)
- Reading-column cloze-marker parity

## Audio pipeline

- **Filename**: `sha1(jp_sentence)[:12].mp3`
- **Voice**: `ja-JP-Neural2-B` (female); set `--voice ja-JP-Neural2-C` for male
- **Idempotent**: re-running only synthesizes new or changed sentences
- **Manifest**: `media/audio_manifest.json`
- Re-run after any content change: `python build_audio.py`

## Anki settings

### FSRS

Use FSRS (Anki ≥ 23.10):

| Setting | Value |
|---------|-------|
| Desired retention | 0.90 |
| Maximum interval | 365 days |
| Easy bonus | 1.30 |
| Hard interval | 1.20 |
| Bury siblings | ON |

Bury siblings keeps recognition + production for the same point from
appearing on the same day.

### Presets

The deck ships with two options presets:

- **Japanese Grammar** — main preset (10 new cards/day, FSRS, sibling burying),
  bound to Module 00 on fresh import.
- **Japanese Grammar (opt-in)** — 0 new cards/day, bound to all other modules.
  Unlock a module by switching its preset to the main one.

### Study path

| Phase | Weeks | Module | Notes |
|-------|-------|--------|-------|
| 1. Foundation | 1–4 | 00 | Kana, particles, copula. Everything else builds on this. |
| 2. N5 grammar | 5–16 | 01 | Core morphology: te-form, -ます, -たい, conditionals |
| 3. N4 grammar | 17–28 | 02 | Passive, causative, giving/receiving, evidentials |
| 4. N3 grammar | 29–44 | 03 | The watershed — half of intermediate Japanese lives here |
| 5. N2 grammar | 45–60 | 04 | News and business prose |
| 6. N1 grammar | 61–80 | 05 | Literary register, abstract relational nouns |

### Card display

- **Show audio button on front** — yes
- **Hide reading on front** — yes (furigana only on back)
- **Auto-play audio on flip** — recommended ON for the first 6 months

## Source authorities

When sources disagree on a point, priority order:

1. **Makino & Tsutsui** — *Dictionary of Basic / Intermediate / Advanced Japanese Grammar* — definitive for N5–N3 nuance
2. **Shin Kanzen Master Grammar** (新完全マスター文法) N1–N5 — JLPT-aligned standard
3. **Martin** — *A Reference Grammar of Japanese* — historical/structural backstop
4. **Imabi.org** + **Tofugu** — cross-checks for modern usage nuance
5. **NHK 日本語発音アクセント新辞典** — pitch accent
6. **Bunpro grammar tree** — master grammar-point checklist (N5 → N1)

## License

Deck content: CC-BY-SA 4.0. Build scripts: MIT.
