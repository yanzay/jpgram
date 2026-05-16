# Changelog

## 0.1.0 — Wave 0 (skeleton)

* Project scaffolding ported from `verbs/` (English Verb System Anki).
* `build_audio.py` — Google Cloud TTS pipeline, JP-specialized
  (default voice `ja-JP-Neural2-B`), auto-loads `.secrets/gcp-adc.json`.
* `normalize_audio.py` — EBU R128 loudness normalization (ffmpeg).
* `build_furigana.py` — JP-specific reading/romaji index using
  pykakasi + fugashi (replaces the English IPA builder).
* `build_anki_package.py` — note-type schema + skeleton packager.
* `validate_anki_data.py` — TSV linter against `NOTE_TYPES` schema.
* `scripts/apply_taxonomy_tags.py` — register/frequency/domain/jlpt/module
  auto-injection.
* [`CONTENT_PLAN.md`](CONTENT_PLAN.md) — full content backbone for
  ~6,500 cards across 14 modules (N5 → beyond N1).
* `grammar/` skeleton with one seed TSV in `00-foundation/` so the
  pipeline is end-to-end testable.

## Roadmap

| Wave | Module | Target cards |
|---|---|---|
| 1 | 00 - Foundation | ~280 |
| 2 | 01 - N5 Grammar | ~560 |
| 3 | 02 - N4 Grammar | ~600 |
| 4 | 03 - N3 Grammar | ~760 |
| 5 | 04 - N2 Grammar | ~880 |
| 6 | 05 - N1 Grammar | ~1040 |
| 7 | 06 - Keigo | ~300 |
| 8 | 07 - Casual / Spoken | ~250 |
| 9 | 08 - Slang & Internet | ~200 |
| 10 | 09 - SFP & Aizuchi | ~120 |
| 11 | 10 - Onomatopoeia | ~600 |
| 12 | 11 - Classical carryover | ~150 |
| 13 | 12 - Beyond N1 | ~600 |
| 14 | 13 - L1 Interference | ~150 × N_L1 |
