# Japanese Grammar Anki Package

A comprehensive Japanese-grammar Anki study package covering **everything** a
learner meets from absolute zero through JLPT N5 → N4 → N3 → N2 → N1 and
beyond — including keigo (honorifics), casual spoken contractions, top-popular
modern slang, sentence-final particles, onomatopoeia, classical-derived
endings still alive in formal modern Japanese, and idiomatic
四字熟語・ことわざ.

> **Status:** Active build. Core content, templates, and package assembly are
> implemented and producing a full `.apkg` export.

## What is included

| File | Purpose |
|------|---------|
| [`CONTENT_PLAN.md`](CONTENT_PLAN.md) | The content backbone — every grammar point, in 16 waves |
| [`GRAMMAR_TAXONOMY.md`](GRAMMAR_TAXONOMY.md) | Cross-reference to Bunpro / Tofugu / Imabi / Shin Kanzen / DJG |
| [`ANKI_SETTINGS.md`](ANKI_SETTINGS.md) | Recommended FSRS settings + study path |
| `build_anki_package.py` | Builds `japanese_grammar_anki.apkg` (auto-runs taxonomy + validation pre-checks, then `validate_apkg.py` post-check) |
| `build_audio.py` | **Tier-2** Google Cloud TTS, one MP3 per unique JP sentence; `--alt-voice` for an optional second-voice track |
| `build_furigana.py` | **Tier-2** furigana + romaji index (pykakasi + fugashi) |
| `build_pitchaccent.py` | **Tier-2** NHK-style pitch-accent index (Kanjium / NHK / Wadoku source chain) |
| `normalize_audio.py` | EBU R128 loudness normalization (ffmpeg) |
| `validate_anki_data.py` | Validates TSV schema, audio refs, placeholder/non-JP source rejection, and point taxonomy coverage |
| `validate_grammar_taxonomy.py` | Validates that every `point:*` tag is mapped in `data/grammar_taxonomy.tsv` |
| `validate_apkg.py` | Post-build integrity check on the packaged `.apkg` |
| `apply_taxonomy_tags.py` | Auto-injects `register:* / jlpt:* / module:* / point:*` tags |
| `requirements.txt` | Pinned Python deps (tier-1 / tier-2 marked) |
| `setup_data.sh` | One-shot downloader for all external resources (idempotent, ~54 MB) |
| `data/README.md` | Map of all external resources + per-subdir READMEs/MANIFESTs |
| `grammar/` | One subdirectory per module; each contains TSVs |
| `draft/` | Schema-only example TSVs, one per note type — NOT shipped |
| `media/audio/` | Generated MP3s — gitignored, restorable via `build_audio.py` |
| `media/furigana_index.json` | Hash → reading lookup — gitignored |
| `media/pitchaccent_index.json` | Token → pitch pattern lookup — gitignored |
| `.secrets/gcp-adc.json` | GCP service-account JSON for TTS — **gitignored** |

## Quick start

```bash
# 1. Install deps (first time only)
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 1a. (Optional, recommended) Pull external data resources
# Downloads ~54 MB into data/ — JMdict, KANJIDIC2, Kanjium + NHK pitch
# accent, JLPT vocab, kanji frequency lists, grammar-ref HTML caches.
# Idempotent. See data/README.md for details + per-file manifests.
bash setup_data.sh

# 2. Inject taxonomy tags + validate corpus
python apply_taxonomy_tags.py
python validate_anki_data.py
python validate_grammar_taxonomy.py

# 2b. Run objective coverage audit (external + internal)
# Optionally resolve exact bunpro:auto/<slug> matches first.
python scripts/resolve_bunpro_exact.py
# Default profile: hard validity gates + practical example thresholds.
python scripts/coverage_audit.py
# Strict profile: also require full Bunpro resolution and multi-note-type spread.
python scripts/coverage_audit.py --enforce-note-types --require-full-bunpro-resolution

# Grammar completeness (reference closure + reverse Bunpro coverage + expansion plan)
python scripts/grammar_completeness_audit.py --skip-bunpro-fetch
# Strict mapping closure (no bunpro:auto debt; exempt rows allowed per reference_closure.json)
python scripts/grammar_completeness_audit.py --skip-bunpro-fetch --require-full-bunpro-resolution

# Parallel strict deck (Bunpro-atomic taxonomy; legacy grammar/ unchanged)
python scripts/setup_strict_deck.py
python3 validate_grammar_taxonomy.py --taxonomy data/grammar_taxonomy_bunpro.tsv --grammar-dir grammar-strict
python scripts/strict_deck_audit.py --skip-bunpro-fetch --require-full-bunpro-resolution

# 3. Render audio (uses .secrets/gcp-adc.json automatically)
python build_audio.py --limit 5 --dry-run                          # cost smoke
python build_audio.py                                              # primary voice
python build_audio.py --alt-voice ja-JP-Neural2-C                  # +optional second voice

# 4. Generate furigana + romaji + pitch-accent indices
python build_furigana.py
python build_pitchaccent.py            # needs data/accents.sqlite (see header)

# 5. Loudness-normalize (optional, recommended)
python normalize_audio.py

# 6. Build the .apkg (also runs validate_anki_data + validate_grammar_taxonomy + validate_apkg automatically)
python build_anki_package.py
```

### Build-pipeline guarantees

`build_anki_package.py` enforces structural checks and performs post-export
verification:
* placeholder audio refs (`[sound:WAVE0_PLACEHOLDER.mp3]`) reach `grammar/`
* placeholder scaffold tokens such as `example*` or malformed `___` usage leak into JP fields
* non-Japanese source text is used for JP audio-source fields (unless explicitly tagged `allow:non-japanese-source`)
* a TSV's header doesn't match its `NOTE_TYPES` schema
* a `point:*` tag is missing from `data/grammar_taxonomy.tsv` or remains coarse (`point:module-*`)
* unresolved audio references are treated as hard failures
* the packaged `.apkg`'s media manifest contains a dangling reference

### Pitch-accent reliability workflow

Use this loop to keep pitch-accent coverage deterministic and measurable:

```bash
# 1) Rebuild token inventory and pitch index
python build_furigana.py
python build_pitchaccent.py

# 2) Enforce baseline quality gates
python validate_pitchaccent_coverage.py \
  --min-coverage 8 \
  --min-weighted-coverage 15 \
  --min-lexical-coverage 9 \
  --min-lexical-weighted-coverage 14 \
  --max-conflicts 2000
```

Operational notes:
* Add human-reviewed corrections to `data/pitch-accent/overrides.json`.
* `build_pitchaccent.py` writes `research-reports/pitchaccent_coverage_report.md`
  with missing/conflict queues ranked by token frequency.
* CI runs the same gate via `.github/workflows/pitchaccent-coverage.yml`.

## Deck hierarchy

See [`CONTENT_PLAN.md`](CONTENT_PLAN.md) for the detailed plan. The
high-level shape:

```
Japanese Grammar
├── 00 - Foundation (kana, particles, copula, counters)
├── 01 - N5 Grammar
├── 02 - N4 Grammar
├── 03 - N3 Grammar
├── 04 - N2 Grammar
├── 05 - N1 Grammar
├── 06 - Keigo (honorifics)
├── 07 - Casual / Spoken Forms
├── 08 - Slang & Internet Speech
├── 09 - Sentence-final particles & aizuchi
├── 10 - Onomatopoeia
├── 11 - Classical / Literary Carryover
├── 12 - Beyond N1 (idioms, 四字熟語, ことわざ)
└── 13 - L1 Interference (per-language)
```

## Card-type matrix

For every grammar point we generate **four** card types:

| Note type | Front | Back |
|---|---|---|
| **Recognition** | JP sentence + 🔊 | label · formula · main use · quick cue · contrast |
| **Production** | English prompt + target form | model JP + reading + why + 🔊 |
| **Cloze** | sentence with `{{c1::…}}` blank | full sentence + reading + hint + 🔊 |
| **Contrast** | sentence + two options (A vs B) | answer + why + tip + 🔊 |

## Audio pipeline

All audio is **deterministically rebuildable** from the TSV corpus:

* Filename = `sha1(jp_sentence)[:12].mp3`
* Manifest (`media/audio_manifest.json`) records voice / rate / sha256
* Re-running `build_audio.py` only synthesizes new or changed sentences
* Default voice: `ja-JP-Neural2-B` (warm female), alt `ja-JP-Neural2-C` (male)

Auth: drop a service-account JSON at `.secrets/gcp-adc.json` (auto-loaded)
or `gcloud auth application-default login`.

## License

The deck content is licensed CC-BY-SA 4.0. The build scripts are MIT.
