# Japanese Grammar Anki Package

A comprehensive Japanese-grammar Anki study package covering **everything** a
learner meets from absolute zero through JLPT N5 → N4 → N3 → N2 → N1 and
beyond — including keigo (honorifics), casual spoken contractions, top-popular
modern slang, sentence-final particles, onomatopoeia, classical-derived
endings still alive in formal modern Japanese, and idiomatic
四字熟語・ことわざ.

> **Status:** Wave 0 (skeleton). Project scaffolding, audio pipeline, and the
> full content plan are in place. Grammar TSVs are generated wave-by-wave per
> [`CONTENT_PLAN.md`](CONTENT_PLAN.md).

## What is included

| File | Purpose |
|------|---------|
| [`CONTENT_PLAN.md`](CONTENT_PLAN.md) | The content backbone — every grammar point, in 14 waves |
| `build_anki_package.py` | Builds `japanese_grammar_anki.apkg` from `grammar/*.tsv` |
| `build_audio.py` | **Tier-2** Google Cloud TTS, one MP3 per unique JP sentence |
| `build_furigana.py` | **Tier-2** furigana + romaji index (pykakasi + fugashi) |
| `normalize_audio.py` | EBU R128 loudness normalization (ffmpeg) |
| `validate_anki_data.py` | Validates TSV structure against `NOTE_TYPES` |
| `scripts/apply_taxonomy_tags.py` | Auto-injects `register:* / frequency:* / domain:*` tags |
| `requirements.txt` | Pinned Python deps |
| `grammar/` | One subdirectory per module; each contains TSVs |
| `media/audio/` | Generated MP3s — gitignored, restorable via `build_audio.py` |
| `media/furigana_index.json` | Hash → reading lookup — gitignored |
| `.secrets/gcp-adc.json` | GCP service-account JSON for TTS — **gitignored** |

## Quick start

```bash
# 1. Install deps (first time only)
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Validate corpus
python validate_anki_data.py

# 3. Render audio (uses .secrets/gcp-adc.json automatically)
python build_audio.py --limit 5 --dry-run        # cost-controlled smoke
python build_audio.py                            # full corpus

# 4. Generate furigana / readings
python build_furigana.py

# 5. Loudness-normalize (optional, recommended)
python normalize_audio.py

# 6. Build the .apkg
python build_anki_package.py
```

## Deck hierarchy (target)

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
