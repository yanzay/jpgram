# Changelog

## 0.2.0 — Wave 0 hardening (post-audit)

Applied four parallel audits (skeleton, content plan, audio pipeline,
premium-grade gap research) and fixed the most impactful findings.

**Skeleton hardening:**
* `validate_anki_data.py` now checks: placeholder-audio-in-grammar/,
  unresolved `[sound:X]` references, cross-corpus excessive reuse, and
  exits non-zero on any failure.
* `validate_apkg.py` (NEW) — post-build integrity check on the packaged
  `.apkg`: media-manifest consistency, orphan-file detection.
* `build_anki_package.py` now drives a real pipeline (taxonomy injection
  → data validation → assembly → apkg validation) and **exits with
  non-zero codes** on every failure mode. CI can now detect broken
  builds.
* `apply_taxonomy_tags.py` promoted to repo root (was orphaned in
  `scripts/`); now invoked automatically by `build_anki_package.py`.
* Seed TSV with placeholder audio refs moved out of `grammar/` into
  `draft/`. The validator hard-rejects placeholder refs that ever
  reach `grammar/`.
* `draft/` (NEW) — schema-only example TSVs for Recognition, Production,
  Cloze, and Contrast note types so content authors have a copy-paste
  template. Excluded from the build.
* `requirements.txt` now clearly tiered (Tier-1 core / Tier-2 optional).

**Audio pipeline upgrades:**
* `build_audio.py` `--alt-voice <name>` flag — each sentence can
  optionally be rendered in a 2nd voice (`<hash>_alt.mp3`) for variety.
* `build_pitchaccent.py` (NEW) — Tier-2 NHK-style pitch-accent index
  builder with a Kanjium → NHK → Wadoku source-priority chain.
  Outputs `media/pitchaccent_index.json`. Card layout overlays the L/H
  contour above the kana on every card whose token is in the index.

**Content plan upgrades** (see `CONTENT_PLAN.md`):
* Card-type matrix extended from 4 to **6** types. Added **Listening**
  (audio-only discrimination) and **Dictation** (fill the blank in a
  displayed frame from audio only).
* Wave 1 (Foundation) expanded from ~280 → **~470 cards**:
  * Pitch accent: 20 → 80 cards (covers all 4 Tokyo classes + compound
    + verb-stem accent shifts on -ます / -て / -た).
  * Particles core: contrast set is now an exhaustive minimal-pair
    matrix (は/が, に/で, へ/に, から/より, や/と/とか, ばかり/だけ/しか).
  * NEW "Verb-group fundamentals" sub-module (る/う dichotomy, why
    -ます exists, vowel harmony in -て/-た).
  * NEW Demonstratives sub-module.
* Wave 3 (N4) restructured into 9 high-confusion sub-clusters with
  explicit card budgets totalling **~720 cards** (was vague):
  voice & valency, conditional 16-cell matrix, **3-sense disambiguated
  -ている**, full -て-aux family (-てある/-ておく/-てしまう/-てみる/
  -ていく/-てくる), giving/receiving + benefactives, evidential cluster
  with negation forms, transitive↔intransitive 40-pair drill, etc.
* Wave 7 (Keigo) expanded to **~400 cards** with explicit table sizes,
  honorific passive stacking, customer-service set phrases, and
  register-shift contrast cards.
* Wave 8 (Casual) expanded with explicit **particle ellipsis** drill
  (which particles drop in casual speech, which don't).
* NEW Wave 14 (Negation paradigm) — cross-module ~120-card sub-deck
  collecting every negative form into a coherent paradigm.
* NEW Wave 15 (Sentence-mining template) — blank TSV templates +
  `MINING_GUIDE.md` so users can add their own immersion sentences
  through the same audio + furigana + pitch-accent pipeline.
* Tagging taxonomy extended with `sense:*` (per-sense disambiguation
  for polysemous points), `confusable-with:*` (explicit cross-link),
  `ambiguity:*`, `complexity:*`, `source:*` (provenance — including
  `source:bunpro`, `source:shin-kanzen`, `source:anime-…` for mined
  sentences), and additional register flavours (feminine-casual,
  masculine-casual).
* `GRAMMAR_TAXONOMY.md` (NEW) — cross-reference of every shipped
  point to Bunpro, Tofugu, Imabi, Shin Kanzen Master, Try!, and the
  Dictionary of Japanese Grammar. Includes a coverage-audit protocol
  to detect missing points before each release.

## 0.1.0 — Wave 0 (skeleton)

* Project scaffolding ported from `verbs/` (English Verb System Anki).
* `build_audio.py` — Google Cloud TTS pipeline, JP-specialized
  (default voice `ja-JP-Neural2-B`), auto-loads `.secrets/gcp-adc.json`.
* `normalize_audio.py` — EBU R128 loudness normalization (ffmpeg).
* `build_furigana.py` — JP-specific reading/romaji index using
  pykakasi + fugashi.
* `build_anki_package.py` — note-type schema + skeleton packager.
* `validate_anki_data.py` — TSV schema linter.
* `apply_taxonomy_tags.py` — tag injector.
* `CONTENT_PLAN.md` — initial 14-wave plan.

## Roadmap (post-audit revised counts)

| Wave | Module | Target cards |
|---|---|---|
| 1  | 00 - Foundation | **~470** |
| 2  | 01 - N5 Grammar | ~600 |
| 3  | 02 - N4 Grammar | **~720** |
| 4  | 03 - N3 Grammar | ~900 |
| 5  | 04 - N2 Grammar | ~1100 |
| 6  | 05 - N1 Grammar | ~1300 |
| 7  | 06 - Keigo | **~400** |
| 8  | 07 - Casual / Spoken | **~300** |
| 9  | 08 - Slang & Internet | ~300 |
| 10 | 09 - SFP & Aizuchi | ~150 |
| 11 | 10 - Onomatopoeia | ~600 |
| 12 | 11 - Classical carryover | ~150 |
| 13 | 12 - Beyond N1 | ~1100 |
| 14 | (cross-module) Negation paradigm | **~120** |
| 15 | 14 - Mining template | template-only |
| 16 | 13 - L1 Interference | ~200 × N_L1 |

**Estimated total:** ~8,200 unique cards across 17 modules
(was ~6,500 in the pre-audit estimate).
