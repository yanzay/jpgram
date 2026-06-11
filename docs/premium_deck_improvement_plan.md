# Premium Deck Status And Improvement Plan

Date: 2026-06-11

## Status

Premium release gate is achieved.

- Corpus: 2,106 TSV files, 12,238 source rows under `grammar-strict/`.
- Full release package: `/tmp/jpgram-premium-full.apkg`.
- Package contents: 12,238 notes/cards, 6,851 media files, 168.51 MB.
- Build mode: full corpus, no excluded or skipped content set.
- Structural validation: pass, 0 errors, 0 warnings.
- Content quality validation: pass under `--strict`, 0 errors, 0 warnings.
- Taxonomy validation: pass, 964 used grammar points mapped.
- Bunpro strict audit: pass, 945/945 Bunpro points covered, 100% reverse coverage.
- Pitch-accent coverage: pass, 9,981 entries, 100.00% weighted coverage.
- Unit tests: pass, 35/35.
- APKG integrity: pass, 0 warnings.

## Completed Improvements

### Content Correctness

- Removed production-card answer leakage from the front template.
- Normalized production `Target` fields so they are form or pattern hints, not full Japanese answers.
- Added validation that blocks production rows where `Target` duplicates `Sample`.
- Fixed high-confidence reading bugs for `辛い` in spicy-food contexts and `昨日本`.
- Added regression tests for those reading cases.
- Corrected N5 explanation drift in `か`, `から`, `で`, `か-or`, `と-with`, `い-adjectives`, `だろう`, and `ませんか`.
- Repaired formula specificity across files that had vague patterns.
- Added focused rows to under-covered recognition and production files so paired grammar points meet the 5-card floor.
- Refined `にしたがって` rows to distinguish proportional change from rule compliance.

### Pedagogy And Comprehensiveness

- Replaced legacy row-balance warnings with a real paired-card floor check.
- Eliminated all row-floor warnings for paired recognition/production grammar points.
- Preserved extra curated examples while requiring a minimum learner-facing coverage floor.
- Tightened content-quality checks so point tags must match their file slug.
- Kept L1 contrast collections exempt from formula-pattern checks where the sentence contrast itself is the teaching mechanism.

### Build And Release Hardening

- Installed the required local Python tooling in `.venv`.
- Installed and initialized Git LFS for this repo.
- Hydrated media and JSON indexes needed for release validation.
- Pointed furigana generation at `grammar-strict/` and made it collect the correct Japanese field per note type.
- Hardened pitch-accent validation so Git LFS pointer files fail with a clear remediation message.
- Removed the builder's `--exclude-broken` mode and all hard-coded broken-file skip lists.
- Added package-build guards for missing audio, Git LFS pointer audio, and invalid MP3 headers.
- Added validation that audio hash filenames match each row's current Japanese source sentence.
- Re-synthesized stale current-text audio refs and filled the remaining L1 contrast audio gaps.
- Added `edge-tts` as a no-auth neural fallback for targeted audio repairs when Google ADC is unavailable.
- Added strict release gates to the package build:
  - `validate_anki_data.py`
  - `validate_content_quality.py --strict`
  - `validate_grammar_taxonomy.py`
  - `validate_pitchaccent_coverage.py`
  - `validate_apkg.py`
- Added `scripts/release_check.py` as a non-destructive one-command premium release gate.
- Updated `scripts/release.sh` to use the same strict validation path before writing a release artifact.
- Fixed taxonomy tag merging so controlled tags such as `complexity:*` are not duplicated.

## Release Gate

Run this before shipping:

```bash
.venv/bin/python scripts/release_check.py --out /tmp/jpgram-premium-full.apkg
```

The gate must pass all of the following checks:

- TSV structure and media manifest validation.
- Strict content-quality validation with zero warnings.
- Grammar taxonomy validation.
- Pitch-accent coverage validation.
- Strict Bunpro audit with full reverse coverage.
- Unit tests.
- Full APKG build with no skipped files.
- APKG integrity validation.

## Ongoing Maintenance Plan

### P0 - Keep Premium Gates Non-Negotiable

Acceptance:
- `scripts/release_check.py` passes before every release.
- New media must be hydrated from LFS before media-sensitive checks run.
- No production front template exposes the answer or the Japanese sample.
- No builder skip list is reintroduced.

### P1 - Protect Grammar Sense Accuracy

Acceptance:
- `MainUse` and `Why` describe the same grammar sense used in the example sentence.
- Ambiguous readings get regression tests before broad regeneration.
- New grammar points include explicit structural formulas rather than bare labels or stems.

### P2 - Preserve Learner Ergonomics

Acceptance:
- Recognition cards train noticing.
- Production cards train retrieval without answer leakage.
- `Why` fields stay short, concrete, and tied to the exact sentence.
- Beginner-level rows avoid unnecessary advanced terminology.

### P3 - Expand Only With Proof

Acceptance:
- New files carry taxonomy tags on every row.
- Paired recognition/production points meet the 5-card floor.
- Added audio is real MP3 content, not an LFS pointer.
- Any intentional exception is encoded in validation, not left as an informal warning.
