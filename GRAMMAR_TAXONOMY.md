# Grammar Taxonomy & Source Cross-Reference

This file maps every grammar point we ship to authoritative external
references so each card can link out for deeper study and so we can
**audit coverage gaps** by diffing our point-set against published
taxonomies.

When a point appears in multiple sources we list all known IDs/URLs;
the first listed is treated as canonical for the purpose of dispute
resolution (see `CONTENT_PLAN.md § Source authorities`).

## Reference taxonomies (canonical orderings we cross-check against)

| Source | Coverage | Slug prefix | Status |
|---|---|---|---|
| **Bunpro grammar tree** | N5 → N1, ~700 points | `bunpro:N5/te-form` | Used as the master grammar-point checklist |
| **Tofugu grammar index** | N5 → N3 (deep dives) | `tofugu:te-form` | Used for explanation/example cross-checking |
| **Imabi.org TOC** | N5 → beyond N1, classical | `imabi:lesson-12` | Authority on classical & literary carryover |
| **Shin Kanzen Master 文法 N1–N5** | N1 → N5 | `shinkanzen:N3/p42` | Authority on JLPT-aligned point lists |
| **Try! N5–N1 文法から伸ばす日本語** | N1 → N5 | `try:N4/u3` | Cross-check for example-sentence selection |
| **Dictionary of {Basic, Intermediate, Advanced} Japanese Grammar** | N5 → N1 | `djg:basic/te-form` | Final authority on nuance disputes (Makino & Tsutsui) |
| **Maggie Sensei grammar archive** | scattered, casual + formal | `maggiesensei:te-mo-ii` | Cross-check for casual register notes |
| **A Reference Grammar of Japanese (Martin)** | structural backstop | `martin:§9.4` | Historical / structural authority |

## Per-point mapping table

The full mapping lives in `data/grammar_taxonomy.tsv` (added in Wave 1
once we start emitting real grammar points). Schema:

```
#columns:point_slug<TAB>jlpt<TAB>module<TAB>bunpro_id<TAB>tofugu_url<TAB>imabi_url<TAB>shinkanzen_ref<TAB>djg_page<TAB>notes
```

Sample rows we'll ship in Wave 1:

```
te-iru-progressive          n5    01-n5    bunpro:N5/te-iru    https://www.tofugu.com/japanese-grammar/te-iru/    imabi:lesson-26    sk:N5-87    djg:basic/te-iru    polysemous: see also te-iru-resultative, te-iru-habitual
te-iru-resultative          n5    01-n5    bunpro:N5/te-iru-resultative    —    imabi:lesson-26    sk:N5-87    djg:basic/te-iru    paired with te-iru-progressive in contrast cards
te-iru-habitual             n5    01-n5    bunpro:N5/te-iru-habitual    —    imabi:lesson-26    sk:N5-87    djg:basic/te-iru    
te-aru                      n4    02-n4    bunpro:N4/te-aru    https://www.tofugu.com/japanese-grammar/te-aru/    imabi:lesson-66    sk:N4-23    djg:intermediate/te-aru    contrast against te-iru-resultative
to-conditional              n4    02-n4    bunpro:N4/to-conditional    https://www.tofugu.com/japanese-grammar/conditional-form-to/    imabi:lesson-114    sk:N4-105    djg:basic/to    contrast cluster: ba/tara/nara
ba-conditional              n4    02-n4    bunpro:N4/ba    https://www.tofugu.com/japanese-grammar/conditional-form-ba/    imabi:lesson-115    sk:N4-106    djg:basic/ba    contrast cluster: to/tara/nara
tara-conditional            n4    02-n4    bunpro:N4/tara    https://www.tofugu.com/japanese-grammar/conditional-form-tara/    imabi:lesson-116    sk:N4-107    djg:basic/tara    contrast cluster: to/ba/nara
nara-conditional            n4    02-n4    bunpro:N4/nara    https://www.tofugu.com/japanese-grammar/conditional-form-nara/    imabi:lesson-117    sk:N4-108    djg:basic/nara    presupposition; contrast cluster
wake-da                     n3    03-n3    bunpro:N3/wake-da    https://www.tofugu.com/japanese-grammar/wake-da/    imabi:lesson-201    sk:N3-44    djg:intermediate/wake    family: wake-de-wa-nai, wake-ga-nai, wake-ni-wa-ikanai
…
```

## Coverage-audit script

`scripts/coverage_audit.py` (Wave 1) will compare:

1. The set of `point:*` tags actually present in our shipped TSVs
2. The set of points listed in `data/grammar_taxonomy.tsv`
3. The set of points expected in each JLPT tier per Bunpro/Shin Kanzen

…and report any point that is **expected but missing** or **shipped
but not classified**. This is run as a hard gate in CI before each
release.

## Maintenance protocol

* Every new grammar point added to `grammar/` must have a row in
  `data/grammar_taxonomy.tsv` *before* the PR merges (enforced by CI).
* Bunpro and Shin Kanzen tables are imported on a yearly cadence via
  `scripts/import_bunpro_index.py` (Wave 2) — they sometimes split or
  merge points (e.g. they recently split `-そう` into `-そう-hearsay`
  vs `-そう-appearance`).
* If two sources disagree on a point's JLPT level (this happens often
  for late N4 / early N3), the canonical level is **the lower of the
  two** (i.e. introduce earlier).
