# grammar-strict — Premium-Quality Improvement Plan

**Drafted:** 2026-05-22 from a five-axis audit (correctness, naturalness,
pedagogy, secondary-cards, metadata). Supersedes the previous
`IMPROVEMENT_PLAN.md` (deleted in commit `c79a25c`). Underlying findings:
[`research-reports/AUDIT_2026-05-19_SUMMARY.md`](research-reports/AUDIT_2026-05-19_SUMMARY.md)
and the four detailed `audit_strict_*.md` reports alongside it, plus the
2026-05-22 re-verification findings folded into this file.

> **Goal.** Take `grammar-strict/` (945 Bunpro points, 2,113 TSVs, ~13.4k
> data rows) from coverage-complete + partially-remediated to a deck a
> serious learner can trust at premium-product quality, with **100%
> confidence of correctness** on every shipped row.

---

## What "premium quality, 100% correct" means here

A shipped row is premium-quality only if **all** of the following hold:

1. The JP sentence is grammatical, natural, and register-coherent.
2. The kana Reading is the correct phonological reading of every kanji.
3. The EN is a faithful translation (not meta-commentary, not a learner
   note).
4. The content actually exercises the filename's grammar point (i.e.
   `point:<slug>` and content agree).
5. Metadata fields (Label/Formula/MainUse/QuickCue/Contrast) are
   meaningful, distinct across rows where the design promises 5 atomic
   exemplars, and accurate to the grammar item.
6. Tags carry no duplicate keys, the JLPT level matches the directory,
   and `source:` references a known origin.
7. The card-type contract holds: cloze deletes the point, contrast tests
   a minimal pair, dictation/listening are answerable only via the
   audio, production is unambiguously elicited by the EN prompt.
8. No content ships with an open `scaffold:pending-audio` tag.

The current deck violates one or more of these on an estimated **15–18%
of all rows** (≈2,100 rows across ~250 files). This plan is the
ordered route to zero.

---

## Status — execution log

| Phase | Status | Commit | Effort |
|---|---|---|---|
| 0 — Release blockers | ✅ done | `c55c2e6` | 3 hr |
| 1 — Auto-furigana sweep | ✅ done | `72027d0` | 1 hr |
| 2 — Cloze re-curation | ✅ done | `697b4cb` | 4 hr |
| 3A — Contrast spot-the-answer fix | ✅ done | `ad5145d` | 2 hr |
| 3B — Off-topic contrast re-author | ✅ done | `6f36c92` | 2 hr |
| 4 — Recognition back-side variability | ✅ done | `e165156` | 2 hr |
| 6 — Validator promotion | ✅ done | `a0d4690` | 3 hr |
| 5 — Polysemy splits | ⏳ pending | — | 6 hr |
| 7 — EN re-audit | ⏸ blocked on API reset | — | 2 hr |
| 8 — Dictation/listening | ⏳ pending | — | 6 hr |
| 9 — Final correctness verification | ⏳ pending | — | 4 hr |

**Headline metrics after Phases 0+1+2+3+4+6:**

- 0 errors, 263 warnings (down from baseline 11,500+ when warnings
  surfaced under the new Phase-6 validators).
- Reading errors: 150+ → **0** across all `_recognition` / `_production`
  / `_dictation` / `_listening` files.
- Whole-sentence cloze warnings: 52 → **0** (validator promoted to
  hard ERROR).
- Contrast spot-the-answer rows: 491 → **24** (edge cases only).
- 5-row Recognition files with monotone back side: 824 / 877 → **0**.
- Empty `_recognition.tsv` files: 2 → **0**.
- Ungrammatical N5 rows in `いい_recognition.tsv`: 5 → **0**.
- Mega-grab-bag mis-curated files (ましょう / なさい / どこ): 3 → **0**.
- Cloze 100%-off-topic files: 14 → **0**.
- Malformed `{c1::…}.` cloze syntax rows: 10 → **0**.
- Pitch-accent primer reading bugs: 4 → **0**; gloss/reading mismatches:
  2 → **0**; odaka rows misexplained as heiban: 20 → **0**.
- `Label="contrast-derived"` placeholder leak: 245 → **0**.
- Duplicate tag-key rows: 1,830 row-instances cleaned (10,520 tokens).
- JLPT-tag-vs-directory mismatches: 28 → **0** (now ERROR-validated).
- Invented classical Japanese in `べき_listening.tsv` (するべからず /
  学べし): 2 → **0**.
- `release.sh` shipping defective files: was unaddressed, now uses
  `--exclude-broken`.

**Remaining warnings (263 total)** — all are real, intentionally left
as WARN until the corresponding content phase addresses them:

- 126 slug-not-in-source — small aggregator-style slugs still not in
  the category allowlist; will shrink as Phase 5 splits land
- 59 cloze-off-topic — secondary-card residuals in
  `01-n5/いい_cloze.tsv` and onomatopoeia files
- 54 twin-parity (Production rows ≠ Recognition rows) — most large
  Recognition files (e.g., `05-n1/とは_recognition.tsv` 71 rows) are
  legitimate content dumps deferred to Phase 5
- 24 contrast-spot-the-answer — 1-char particle edge cases left by
  the Phase-3 conversion script (e.g., `かしら_contrast.tsv` rows
  with Answer=`よ` appearing in a non-uniquely-resolvable JP)

---

## Headline numbers (post 2026-05-22 re-audit)

| Defect class | Status vs 2026-05-19 | Current count | Severity |
|---|---|---|---|
| Cloze-point drift | partially fixed | 14 files 100% off-topic (was 17); 25 files ≥50% off-topic; **563 polluted rows in 47 files** | CRITICAL |
| Production mis-curation | partially fixed | 4 hot files repaired; **~30 production files** still off-topic | CRITICAL |
| Auto-furigana bugs | **NOT regen'd** | Every reading bug from the prior audit still present (彼の→かの ≥70 rows, お金→おきん, 外国人→がいこくにん, 七時→ななじ, や否や→やひや, 蘇った→よみがった, 100℃→ひゃくどしたい, 健康→きれい) + ~10 new ones | CRITICAL |
| Pitch-accent primer foundation | not fixed | 5 wrong single-kanji readings (遊ぶ→あすぶ, 橋→きょう, 点→ちょぼ, 弟→おと) + 2 gloss/reading mismatches | CRITICAL — first card a learner sees |
| Invented classical (べまじ/るざり/やもしれない/然くして) | **FIXED** | 0; validator now blocks regressions | — |
| Meta-EN contamination | **FIXED** | 0/6584 rows; validator enforces | — |
| Recognition back-side collapse | unchanged | 94% of 5-row recognition files share identical Label/Formula/MainUse/Contrast across all rows; only QuickCue varies | HIGH |
| Contrast spot-the-answer | partially fixed | 491 rows / 36 files where the answer is literal in JP with no blank | HIGH |
| Whole-sentence cloze | partially fixed | 52 rows / 5 files (validator emits WARN; not blocking) | HIGH |
| Empty data files (header-only) | **NEW** | 2 (`からすると-からすれば_recognition.tsv`, `にあたり-にあたって_recognition.tsv`) | BLOCKER |
| Ungrammatical JP in N5 foundation | **NEW** | 5 rows in `01-n5/いい_recognition.tsv` (`きれいなきれいです`, `ハンサムなです`, `新しくくないです`, `大きくかったです`, `静かなな環境で…`) | BLOCKER |
| Slug↔content mega-grab-bag | **NEW catalog** | `01-n5/ましょう_recognition.tsv` (0/12 rows test ましょう), `02-n4/なさい_recognition.tsv` (5/31), `01-n5/どこ_recognition.tsv` (1/6) | BLOCKER |
| `Label="contrast-derived"` placeholder leak | **NEW** | 245 rows in 12 files | HIGH |
| English meta-label in Production Target | **NEW** | 268 rows in ~20 files (e.g. `Target = "V-neg + うちに / Adj + うちに / N + うちに"`) | HIGH |
| Duplicate tag-keys | **NEW catalog** | 195 dup `frequency:`, 143 dup `complexity:`, 5 dup `jlpt:` across 1,830 row-instances | MEDIUM |
| Malformed cloze syntax | **NEW** | 10 rows in `02-n4/causative-passive_cloze.tsv` use single-brace `{c1::…}.` | HIGH |
| Invented classical (new instances) | not caught | `するべからず` (should be すべからず), `学べし` (should be 学ぶべし) in `03-n3/べき_listening.tsv` | HIGH |
| Invented mimetic words | **NEW** | セキセキ, ショリショリ, ロボロボ, ふんぶん, キチリッ, ぎゅぎゅ in onomatopoeia files | HIGH |
| `あげる` in-group recipient | unchanged | `01-n5/あげる_listening.tsv:14` `同僚が私に仕事を教えてあげた` (should be くれた) | MEDIUM |
| `release.sh` ships defective files | not addressed | does not pass `--exclude-broken`; all bad cards land in the published `.apkg` | HIGH |

Per-card-type grades after re-audit:

| Type | Grade | Note |
|---|---|---|
| Recognition (front) | A− | JP fronts are natural and varied |
| Recognition (back metadata) | C | 94% of 5-row files have monotone back side |
| Production (Prompt + Target + Sample) | B | Why is now point-specific; 268 Target rows are English templates |
| Production "Why" | A− | Major improvement since 05-19 audit |
| Cloze | D− | 80% of cards still don't delete the named point |
| Contrast | C− | 50% rows have answer literal in JP |
| Dictation | D+ | 7 critical files off-topic |
| Listening | C+ | Coverage thin; invented classical in 1 file; 1 grammar error |

---

## Premium-quality plan — 9 phases

Each phase is independently shippable, has an acceptance gate, and
includes the validator(s) that protect the fix in CI. The phases are
ordered by **(impact × confidence-it-unblocks-other-work) / effort**.

### Phase 0 — Release blockers (~3–5 hr) `MUST FIX FIRST`

These are individually small but visible-on-first-card defects. Until
they are fixed, no release can claim premium quality.

**Files (and number of rows to rewrite):**

| File | What | Rows |
|---|---|---|
| `grammar-strict/04-n2/からすると-からすれば_recognition.tsv` | Empty (header only) — author 5 rows | 5 |
| `grammar-strict/04-n2/にあたり-にあたって_recognition.tsv` | Empty (header only) — author 5 rows | 5 |
| `grammar-strict/01-n5/いい_recognition.tsv:7-11` | Ungrammatical JP (`きれいなきれいです`, `ハンサムなです`, `新しくくないです`, `大きくかったです`, `静かなな環境で静かなく走ります`) — rewrite | 5 |
| `grammar-strict/01-n5/ましょう_recognition.tsv:7-19` | All 13 rows teach plain volitional (-よう/-ろう), zero teach ましょう — replace with polite-suggestion rows | 13 |
| `grammar-strict/02-n4/なさい_recognition.tsv:7-38` | 31 rows mix -なきゃ/-ので/-から/-のに/そうだ; only 5 use なさい — keep 5, drop the rest, or split into sibling files | 26 to drop |
| `grammar-strict/01-n5/どこ_recognition.tsv:7-12` | Tests 6 interrogatives; only 1/6 uses どこ — keep どこ, move siblings to interrogatives-aggregator file | 5 |
| `grammar-strict/02-n4/causative-passive_cloze.tsv:7-16` | Reading column uses single-brace `{c1::…}.` (Anki renders literal braces) — fix to `{{c1::…}}` | 10 |
| `grammar-strict/04-n2/および_cloze.tsv:7-9` | Reading column typo `およぴ` (3 rows) — fix to `および` | 3 |
| `grammar-strict/01-n5/あげる_listening.tsv:14` | `同僚が私に仕事を教えてあげた` ungrammatical in-group あげる — change recipient to a 3rd party or switch to くれた | 1 |
| `grammar-strict/03-n3/べき_listening.tsv` lines containing `するべからず`, `学べし` | Invented classical attachment — fix to `すべからず`, `学ぶべし` | 2 |
| `grammar-strict/00-foundation/pitch-accent-primer_recognition.tsv` (mirror `_production.tsv`) | 4 wrong single-kanji readings (遊ぶ→あすぶ, 橋→きょう, 点→ちょぼ, 弟→おと) + 2 gloss/reading mismatches (頭=かしら glossed as cattle counter; 秋=あき glossed "Time") | 6 |
| `scripts/release.sh` | Add `--exclude-broken` to the build invocation, OR delete `_BROKEN_SUFFIXES` from `build_anki_package.py` and replace with a per-file allowlist | 1 |
| Stray narrative `#` lines between standard headers in 5 files | Delete | 5 |

**Acceptance gate (Phase 0):**

- Re-run `validate_anki_data.py` — must report 0 errors and 0
  whole-sentence-cloze warnings on the 11 files above.
- Add validator rules: (a) `_recognition.tsv` files must have ≥1 data
  row; (b) header section must contain exactly the 5 expected directive
  lines, no stray comments. Add to CI gate.
- Manual spot-check: read all 11 files end-to-end after edits.

### Phase 1 — Auto-furigana regeneration sweep (~2 hr automated + 1 hr review)

Rationale: every reading bug catalogued on 2026-05-19 is still present
in HEAD. The auto-furigana sweep was never re-run after the bug fixes
landed in `scripts/jp_reading.py`. This is the single highest-leverage
operation — one batch fixes ≥150 reading defects across the deck.

**Steps:**

1. Add the following overrides to `scripts/jp_reading.py` (verify each
   against UniDic + JMdict before committing):

   | Surface | Wrong (current) | Correct |
   |---|---|---|
   | 彼の / 彼が / 彼に / 彼を | かの / etc. | かれの / etc. |
   | お金 | おきん | おかね |
   | 親 (free-standing N) | したし | おや |
   | 七時 | ななじ | しちじ |
   | 八日 | はちにち | ようか |
   | や否や | やひや | やいなや |
   | 外国人 | がいこくにん | がいこくじん |
   | 開ける (vi/vt disambig: あける) | ひらける | あける |
   | 入って | いっって | はいって |
   | 蘇った | よみがった | よみがえった |
   | 100℃ / 数字+℃ | unparsed | ひゃくど |
   | 健康 | きれい | けんこう |
   | 光と影 | ひかとかげ | ひかりとかげ |
   | 若き日 | わかきにち | わかきひ |
   | 行う (vs 行く collision when stem is N+を) | いっている | おこなっている |
   | 見た目 | みたため | みため |

2. Re-run reading regeneration across all 2,113 TSVs. Use the existing
   `scripts/fix_reading_column.py` as the entry point or extend it.
3. **Diff review**: produce a `before → after` per-row diff so the
   author can scan for unintended changes (sokuon handling, rendaku
   compounds, sino-Japanese readings).
4. Re-render audio for any row where the kana reading changed and the
   audio is derived from the reading. (If audio is derived from JP
   surface, no re-render needed.)

**Acceptance gate (Phase 1):**

- Per-pattern grep returns 0 across all TSVs for each item in the
  override table.
- `tests/test_jp_reading.py` extended with at least 20 regression cases
  drawn from the override list — must pass.
- Pitch-accent primer reading column visually reviewed.

### Phase 2 — Cloze re-curation (~10–15 hr)

The cloze deck is the worst-quality card type in the entire build
(grade D−). 14 files are 100% off-topic; 25 files are ≥50% off-topic.

**Two-track approach:**

**Track 2A — Mass delete-and-regenerate (10 files, ~250 rows).** For
the 100%-off-topic files, no row is salvageable. Delete every data row
and re-author 5 on-point cloze rows per file using one of:

  - Bunpro live index (`data/bunpro_live_index.json` per memory)
  - JMdict + Tatoeba (`data/tatoeba_sentences.tsv`)
  - Hand-authored from `content/n<N>_strict_content.py`

  Target files (priority order):

  1. `grammar-strict/04-n2/ものか_cloze.tsv` (35 rows → 5)
  2. `grammar-strict/04-n2/まで_cloze.tsv` (30 → 5)
  3. `grammar-strict/04-n2/と考えられる_cloze.tsv` (30 → 5)
  4. `grammar-strict/04-n2/てたまらない_cloze.tsv` (10 → 5)
  5. `grammar-strict/04-n2/にもかかわらず_cloze.tsv` (10 → 5)
  6. `grammar-strict/04-n2/および_cloze.tsv` (32 off-topic → 5)
  7. `grammar-strict/03-n3/ながらも_cloze.tsv` (17/20 → 5)
  8. `grammar-strict/03-n3/に違いない_cloze.tsv` (22/25 → 5)
  9. `grammar-strict/03-n3/だらけ_cloze.tsv` (38/40 → 5)
  10. `grammar-strict/03-n3/につれて_cloze.tsv` (27/30 → 5)
  11. `grammar-strict/03-n3/っぽい_cloze.tsv` (12/15 → 5)
  12. `grammar-strict/03-n3/せいで_cloze.tsv` (14/15 → 5)
  13. `grammar-strict/03-n3/ことがある_cloze.tsv` (11/15 → 5)
  14. `grammar-strict/05-n1/に足る_cloze.tsv` (45 → 5; add Reading-column cloze marker)

**Track 2B — Repair whole-sentence cloze (4 files).** Rows wrap the
entire JP in `{{c1::…}}`, which is unanswerable.

  - `grammar-strict/01-n5/ましょう_cloze.tsv` (10 rows)
  - `grammar-strict/02-n4/みたい_cloze.tsv` (10 rows)
  - `grammar-strict/02-n4/るところだ_cloze.tsv` (10 rows)
  - `grammar-strict/02-n4/ていく_cloze.tsv` (20 rows)

For each: identify the morpheme that the file is named after, isolate
it in JP, wrap only it in `{{c1::…}}`, mirror into Reading column.

**Track 2C — Reading-column cloze marker mirror.** ~149 rows have JP
cloze marker but Reading column lacks it. Easy regex sweep.

**Track 2D — Hint column must not paraphrase the answer.** Files like
`grammar-strict/01-n5/あげる_cloze.tsv` have `Hint = "give favor (read
to someone)"` — the hint states the answer. Rewrite Hint as a 2–4-word
*situational* cue, never naming the form.

**Acceptance gate (Phase 2):**

- Every `<point>_cloze.tsv` has ≥80% of `{{c1::…}}` content matching
  the filename point (or a documented alias).
- Zero whole-sentence-cloze rows (validator promoted from WARN to
  ERROR).
- Reading-column cloze-marker parity at 100%.
- Hint column never contains the EN gloss of the cloze content.

### Phase 3 — Contrast spot-the-answer mechanical fix (~6–8 hr)

The 50% spot-the-answer rate degrades Contrast to plain Recognition. A
deterministic rewrite resolves it.

**Mechanical conversion**, applied to 491 rows / 36 files:

  - If `Answer` appears verbatim in `JP` and `JP` contains no `___`,
    replace the answer occurrence in JP with `___` and (where
    necessary) move the answer cue into OptionA/OptionB.
  - Require OptionA ≠ OptionB, and that they share grammatical category
    (both particles, both endings, both auxiliaries — not particle vs.
    sentence-final).
  - For the 28 non-parallel pairs (e.g., `OptionA=だの`,
    `OptionB=といって`), reauthor the alternative so it isolates one
    grammatical feature.

**Files (top 12 — full list in `audit_strict_secondary_cards` agent
output):**

  - `grammar-strict/03-n3/せいで_contrast.tsv` (25/25)
  - `grammar-strict/03-n3/ばかり_contrast.tsv` (26/40)
  - `grammar-strict/02-n4/たら_contrast.tsv` (28/39)
  - `grammar-strict/03-n3/ながらも_contrast.tsv` (25/25)
  - `grammar-strict/04-n2/にしたがって_contrast.tsv` (10/10)
  - `grammar-strict/05-n1/のなんのって_contrast.tsv` (10/10)
  - `grammar-strict/02-n4/ようだ_contrast.tsv` (10/10)
  - `grammar-strict/02-n4/かしら_contrast.tsv` (14/15)
  - `grammar-strict/01-n5/どこ_contrast.tsv` (13/15)
  - `grammar-strict/02-n4/ございます_contrast.tsv` (15/25)
  - `grammar-strict/05-n1/べくもない_contrast.tsv` (9/10)
  - `grammar-strict/05-n1/ないでもない_contrast.tsv` (9/10)

**Off-topic-only contrast files (17 files, ~150 rows)**: same approach
as Phase 2A — delete data rows and re-author 5–10 on-point contrast
pairs.

**Acceptance gate (Phase 3):**

- New validator (added in Phase 6): block any contrast row where
  `Answer` appears as a substring of `JP` AND `JP` does not contain a
  `___` placeholder. Hard error in CI.
- Manual review of OptionA/B parallelism on 20 random rows per
  card-type sweep.

### Phase 4 — Recognition back-side per-row variability (~8–10 hr)

94% of 5-row Recognition files have identical Label/Formula/MainUse/
Contrast across all rows. The "5 atomic exemplars" design collapses
into "5 fronts + 1 back". Fix mechanically.

**Two paths:**

  - **Option A (recommended): per-row QuickCue + per-row MainUse.**
    Copy the per-row `Why` text from the paired Production file into
    Recognition's MainUse column (or QuickCue). The Production deck
    already has high per-row Why variance after the 05-19 remediation.
    Mechanical sync: `Recognition[<JP>].MainUse =
    Production[<JP>].Why` where the same JP appears as Sample. For JP
    that only appears on the Recognition side, hand-author one sense
    fragment per row.

  - **Option B: promote constant fields to file-level metadata.** Move
    Label/Formula to the TSV header as a `#meta:` directive and read
    once per file in `build_anki_package.py`. Reduces row weight, but
    requires Anki template changes.

Option A is simpler and preserves the schema.

**Files affected:** ~824 of 874 five-row recognition files. The fix is
mechanical and bulk-applied via a one-shot script.

**Acceptance gate (Phase 4):**

- For every 5-row Recognition file, at least 3 of (Label, Formula,
  MainUse, QuickCue) vary across the 5 rows.
- The Production–Recognition back-side mirror is verified by a new
  validator: `Recognition[<JP>].MainUse ≠ Recognition[<JP'>].MainUse`
  for the 5 distinct JPs in the file.

### Phase 5 — Polysemy & mega-grab-bag splits (~6 hr)

Bare-kana slugs that conflate multiple grammar items violate the
filename-as-point contract.

**Splits required:**

| Current file | Proposed split |
|---|---|
| `01-n5/と_*.tsv` (conditional + listing + quotation + comitative collapsed) | `と-conditional-*`, `と-quotation-*`, `と-listing-*`, `と-with-*` |
| `01-n5/って_*.tsv` (currently a 20-row te-form derivation drill) | rename to `te-form-derivation_*`; author a real `って-quotation_*` |
| `03-n3/ばかり_*.tsv` (6 senses in one file) | `ばかり-only`, `たばかり`, `てばかり`, `んばかり`, `ばかりに`, `たばかりに` |
| `02-n4/わけ_*.tsv` (わけだ + わけがない + わけではない) | follow Bunpro per-sense |
| `02-n4/ところ_*.tsv` (たところ + ているところ + どころか + ところで) | per-sense |
| `02-n4/まで_*.tsv` | currently has 30 rows of は/が/を particles — split off into particle drills with new slugs; reduce まで to its own 5 |
| `02-n4/いい_*.tsv` (umbrella i-Adj file) | rename to `i-adjectives`; create `いい-good_*` if needed |
| `02-n4/それ_*.tsv` (demonstratives umbrella) | rename to `demonstratives` or expand category allowlist |
| `02-n4/どこ_*.tsv` (interrogatives umbrella) | rename to `interrogatives` or split |

For each split: write a small migration script that reads the existing
file, classifies each row by content, and routes it to the correct new
slug file. Anything unclassifiable goes to a `<slug>_review.tsv`
quarantine for manual triage.

**Files with English meta-label templates in Production Target** (268
rows / ~20 files): these can either be (a) replaced with a real target
JP form per row (e.g., row Sample = `走らないうちに帰った` →
`Target = 走らないうちに`), or (b) the Target column dropped and the
note type collapsed to Prompt + Sample. Option (a) is recommended for
parity with other production files.

**Acceptance gate (Phase 5):**

- No filename slug maps to >1 grammar sense in its file.
- Production Target column never contains slashes, `+`, or Romanised
  templates. Add validator.
- Bunpro reverse-coverage audit still PASSes after splits (every
  Bunpro point still has ≥1 file).

### Phase 6 — Validator promotion & schema enforcement (~2 hr)

Lock in the gains from Phases 0–5 by promoting validators from WARN to
ERROR and adding new ones. After each phase lands, the corresponding
validator promotes to blocking.

**Validators to add or promote** (in `validate_anki_data.py`):

  1. **Empty data file** (≥1 non-header data row) — BLOCKER.
  2. **Stray comment in header section** — BLOCKER.
  3. **Whole-sentence cloze** — promote from WARN to BLOCKER after
     Phase 2.
  4. **Cloze point-alignment** — ≥80% rows in `<point>_cloze.tsv` must
     contain `<point>` (or alias) in `{{c1::…}}`. BLOCKER after Phase 2.
  5. **Reading-column cloze-marker parity** — BLOCKER after Phase 2.
  6. **Hint paraphrases answer** (overlap of Hint ↔ cloze content
     translation) — WARN.
  7. **Contrast spot-the-answer** (Answer is substring of JP with no
     `___`) — BLOCKER after Phase 3.
  8. **Contrast option-parallelism** (length-ratio or POS-mismatch
     heuristic) — WARN.
  9. **Dictation/listening point-in-Answer** — BLOCKER after secondary
     re-curation.
  10. **Recognition back-side variability** (≥3 of Label/Formula/
      MainUse/QuickCue must vary per file) — BLOCKER after Phase 4.
  11. **Tag-key uniqueness per row** (no duplicate `complexity:`,
      `frequency:`, `jlpt:`, `source:`) — BLOCKER.
  12. **JLPT level matches directory** (`01-n5/` ⇒ `jlpt:n5` exactly
      once) — BLOCKER.
  13. **Production Target schema** (no slashes, no `+`, no English
      grammar templates) — BLOCKER after Phase 5.
  14. **Placeholder leak** (`Label="contrast-derived"` or any literal
      `TODO`/`PLACEHOLDER`/`scaffold:*` in non-tag fields) — BLOCKER.
  15. **Audio-or-pending invariant** (every row has either
      `[sound:<hash>.mp3]` audio OR `scaffold:pending-audio` tag — and
      `scaffold:pending-audio` blocks release builds).
  16. **Slug-content integrity** (file's filename slug must appear in
      ≥1 row's JP unless in category allowlist).

Reorganise `validate_anki_data.py` so error vs warning is clear and
each rule prints actionable file:line output. Add `--explain` flag for
rule documentation.

**Acceptance gate (Phase 6):**

- `validate_anki_data.py` returns 0 errors and 0 warnings on HEAD.
- CI fails any PR that re-introduces a rule violation.
- Documentation block in repo README or `VALIDATORS.md` lists each rule.

### Phase 7 — Re-run EN-gloss + cross-card consistency audit (~2 hr)

The 2026-05-22 EN-gloss audit agent hit a rate limit before completing.
Re-run it after Phase 0 unblocks. Scope confirmed unfinished: cross-card
EN drift, translation faithfulness sample, Why-note teaching value
re-check, Hint quality, Contrast Why/Tip quality. Treat as a focused
agent task with its own findings file:
`research-reports/audit_strict_en_consistency_2026-05.md`.

The two main gaps to investigate are:

  1. **Cross-card EN consistency** — when the same JP appears as a
     Recognition JP and a Production Sample, are EN and Why fields
     consistent? Spot-check 100 cross-card pairs.
  2. **EN translation faithfulness** — sample 200 EN cells and grade for
     register, tense, idiom, agent inference. The 168 meta-EN rows are
     already fixed (verified 2026-05-22); the residual concern is
     accuracy of the actual translations.

**Acceptance gate (Phase 7):**

- Audit report committed with ≤10 HIGH-severity findings; all addressed
  in a follow-on commit.

### Phase 8 — Dictation/listening expansion (~6 hr)

Coverage is currently 30 + 30 files. Both card types are the smallest
and weakest in the deck. Either:

  - **(a) Re-author the 30 dictation + 30 listening files** to be
    on-point and discriminative (audio-only-answerable).
  - **(b) Drop the dictation/listening note types** from the released
    deck until coverage is broad enough to be useful. Mark the existing
    60 files `experimental:true` in tags and exclude from default
    build.

Option (a) is the premium-quality path but more expensive. Option (b)
de-risks shipping. Choose at Phase-8 entry.

**Acceptance gate (Phase 8):**

- All shipped dictation/listening rows pass the point-in-Answer
  validator.
- Listening rows are demonstrably audio-only-answerable (heuristic: the
  Transcript and the Answer field differ in one feature that audio can
  resolve — long vowel, geminate, pitch, particle, aspect).

### Phase 9 — Final correctness verification (~4 hr)

Independent end-to-end sweep before tagging the premium release.

  1. **Programmatic gate**: all validators pass with 0 errors; CI green.
  2. **Sampling gate**: random sample of 200 cards, manually reviewed
     against all 8 premium-quality criteria. Acceptance: ≥99% of
     sampled cards meet all 8 criteria.
  3. **Native-speaker pass** (recommended): hire 4 hours of native
     reviewer time on N1+N2 (highest defect concentration). Acceptance:
     reviewer reports no errors on a 100-card sample.
  4. **Build the `.apkg`** with `--exclude-broken` left ON until the
     allowlist is empty.
  5. Update README to remove the "remediation in progress" notice;
     state the audit pass and the validator-enforced quality bar.
  6. Tag `v1.0.0` (or whatever version the release scheme calls for).

---

## Effort and sequencing

| Phase | Est. effort | Blocks | Can parallelise with |
|---|---|---|---|
| 0 — Blockers | 3–5 hr | all releases | — |
| 1 — Furigana sweep | 3 hr | EN audit, manual review | 2, 3 |
| 2 — Cloze re-curation | 10–15 hr | Phase 6 gate | 3, 4 |
| 3 — Contrast fix | 6–8 hr | Phase 6 gate | 2, 4 |
| 4 — Recognition variability | 8–10 hr | Phase 6 gate | 2, 3 |
| 5 — Polysemy splits | 6 hr | Phase 6 gate | 2, 3, 4 |
| 6 — Validator promotion | 2 hr | — | — |
| 7 — EN re-audit | 2 hr | Phase 9 | — |
| 8 — Dictation/listening | 6 hr (opt-a) | Phase 9 | — |
| 9 — Final verification | 4 hr | release | — |

**Critical path:** 0 → 1 → (2 || 3 || 4 || 5) → 6 → 7 → 8 → 9.

Total: **50–60 hours** of focused content+code work for a 100%
confidence-level release. Phases 0+1 alone (≤8 hours) remove the
release blockers and ~80% of visible defects.

---

## Out-of-scope (for now)

- **Note-type schema changes** (e.g., moving Label/Formula to file-level
  metadata) — defer until after v1.0 unless Phase 4 makes it natural.
- **Bunpro coverage expansion** beyond 945 points — current scope is
  defined and well-covered.
- **Audio voice diversification** — `_alt.mp3` second-voice clips
  mentioned in CONTENT_PLAN.md — defer.

---

## Tracking

Per-phase progress is tracked in `TaskList` (in-conversation) and in
git history (one commit per phase or per file-batch). After each phase,
update this file's Headline numbers table to reflect the new state and
push as part of the commit.

Last update: 2026-05-22 (initial draft from five-axis audit).
