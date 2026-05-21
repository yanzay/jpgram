# Japanese Grammar Anki Package (Strict Deck)

A Bunpro-atomic Japanese-grammar Anki deck covering all 945 Bunpro grammar
points from N5 through N1, with two primary card types per point:
**Recognition** and **Production**, plus secondary Cloze / Contrast /
Dictation / Listening cards on a subset of points.

> **Status:** Coverage 100% (945/945 Bunpro points). **Content-quality
> remediation in progress** — see
> [`research-reports/AUDIT_2026-05-19_SUMMARY.md`](research-reports/AUDIT_2026-05-19_SUMMARY.md)
> and [`IMPROVEMENT_PLAN.md`](IMPROVEMENT_PLAN.md). Until Phase 2 lands,
> ~70% of secondary cards (cloze/dictation/listening) and ~12% of production
> files have known content/filename drift. The `coverage_audit.py` gate
> verifies row counts, not row quality.

## Coverage

| Level | Points | Files |
|-------|--------|-------|
| N5 | 122 | `grammar-strict/01-n5/` |
| N4 | 160 | `grammar-strict/02-n4/` |
| N3 | 194 | `grammar-strict/03-n3/` |
| N2 | 203 | `grammar-strict/04-n2/` |
| N1 | 169 | `grammar-strict/05-n1/` |
| **Total** | **945** | |

Foundation cards (kana, particles, copula) live in `grammar-strict/00-foundation/`.

## Card types

| Note type | Front | Back |
|---|---|---|
| **Recognition** | JP sentence + 🔊 | label · formula · main use · quick cue · contrast |
| **Production** | English prompt + target form | model JP + reading + why + 🔊 |

Fields: `JP · Reading · EN · Label · Formula · MainUse · QuickCue · Contrast · Audio · Tags`

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

data/
  grammar_taxonomy_bunpro.tsv  Bunpro slug → point metadata
  grammar-refs/                Cached Bunpro index JSON

build_anki_package.py   Assembles grammar-strict/ → japanese_grammar_strict.apkg
build_audio.py          Google Cloud TTS: one MP3 per unique JP sentence (idempotent)
```

## Quick start

```bash
# 1. Install deps
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Verify deck integrity
.venv/bin/python scripts/strict_deck_audit.py

# 3. Build Anki package
python build_anki_package.py

# 4. (Optional) Generate audio — requires GCP credentials
# Drop service-account JSON at .secrets/gcp-adc.json or use:
#   gcloud auth application-default login
python build_audio.py --dry-run    # cost preview
python build_audio.py              # synthesize all sentences
```

## Adding / updating content

Content lives in `content/<level>_strict_content.py` as a Python `CONTENT` dict.
Each entry has `label`, `formula`, `main_use`, `contrast`, and `sentences`
(target: 5 atomic sentences per point, each with `jp`, `en`, `why` ≤ 8 words).
Some legacy files exceed the 5-sentence cap and are tracked in the
improvement plan.

After editing a content file, regenerate:

```bash
.venv/bin/python scripts/generate_strict_content.py \
    --content content/<level>_strict_content.py \
    --module <module>    # e.g. 01-n5, 02-n4, …, 05-n1
```

## Audio pipeline

* Filename: `sha1(jp_sentence)[:12].mp3`
* Re-running `build_audio.py` only synthesizes new/changed sentences
* Default voice: `ja-JP-Neural2-B` (female), alt `ja-JP-Neural2-C` (male)
* Manifest: `media/audio_manifest.json`

## Audit

```bash
.venv/bin/python scripts/strict_deck_audit.py
# Expected: strict_deck_audit: exit=0  bunpro_reverse_coverage: pct=100.0% covered=945/945
```

**This script checks coverage only, not content quality.** For the
content-quality audit and remediation roadmap see:

- [`research-reports/AUDIT_2026-05-19_SUMMARY.md`](research-reports/AUDIT_2026-05-19_SUMMARY.md) — top-level findings
- [`research-reports/audit_strict_correctness.md`](research-reports/audit_strict_correctness.md) — Japanese grammar/readings
- [`research-reports/audit_strict_pedagogy.md`](research-reports/audit_strict_pedagogy.md) — card-design pedagogy
- [`research-reports/audit_strict_secondary_cards.md`](research-reports/audit_strict_secondary_cards.md) — cloze/contrast/dictation defects
- [`research-reports/audit_strict_en_consistency.md`](research-reports/audit_strict_en_consistency.md) — English glosses + cross-card consistency
- [`IMPROVEMENT_PLAN.md`](IMPROVEMENT_PLAN.md) — prioritized fix roadmap

## License

Deck content: CC-BY-SA 4.0. Build scripts: MIT.
