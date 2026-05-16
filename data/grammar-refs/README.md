# Grammar References

This directory contains curated external grammar references used for coverage auditing and cross-validation of our shipped grammar taxonomy.

## Files Overview

### Index Files (JSON)

- **bunpro_grammar_index.json** — Bunpro grammar point reference (placeholder; requires manual curation)
  - Status: ⚠️ **Manual curation needed**
  - Format: Expected `{ points: [ { point_slug, jlpt_level, url, summary } ] }`
  - Source: https://bunpro.jp/grammar_points
  - Note: Bunpro has no official API; community scrapes exist but are not currently available

- **tofugu_grammar_index.json** — Tofugu grammar TOC index (structure only)
  - Status: 📋 **Ready for parsing**
  - Format: Structure ready; awaiting extraction from cached HTML
  - Source: https://www.tofugu.com/japanese-grammar/
  - Cached HTML: `tofugu_grammar_toc.html`

- **imabi_grammar_index.json** — Imabi syllabus index (structure only)
  - Status: 📋 **Ready for parsing**
  - Format: Structure ready; awaiting extraction from cached HTML
  - Source: https://www.imabi.org/
  - Cached HTML: `imabi_toc.html`
  - License: CC-BY-NC (non-commercial use only)

### HTML Caches

- **tofugu_grammar_toc.html** — Raw HTML from Tofugu grammar guide (77.6 KB)
- **imabi_toc.html** — Raw HTML from Imabi syllabus (currently incomplete; JS rendering may be required)

### Grammar Level Lists

- **jlpt-grammar/** — Directory for JLPT N1–N5 grammar lists
  - Status: ❌ **Not available** (GitHub source repos return 404)
  - Intended format: Per-level JSON files (`jlpt_N1.json`, `jlpt_N2.json`, etc.)
  - Expected schema: `{ level: "N1", points: [ { kanji, kana, english, examples } ] }`

### Documentation Files

- **UNIDIC_NOTES.txt** — Notes on UniDic full dictionary availability
  - Full UniDic-CWJ (~2 GB) not included
  - User installation: `pip install unidic && python -m unidic download`
  - License: CC-BY-SA-4.0

- **CC100_NOTES.txt** — Notes on CC-100 Japanese corpus
  - Full corpus (~15 GB compressed) not included
  - Reference: https://data.statmt.org/cc-100/ja.txt.xz
  - License: CC-BY-4.0

## Cross-Reference with GRAMMAR_TAXONOMY.md

Our main grammar taxonomy is in `grammar/GRAMMAR_TAXONOMY.md` (root level). The coverage audit workflow will:

1. **Load shipped points** from `grammar/GRAMMAR_TAXONOMY.md`
2. **Compare against external sources**:
   - Bunpro points (when `bunpro_grammar_index.json` is populated)
   - JLPT level assignments (when `jlpt-grammar/*.json` is available)
   - Tofugu/Imabi cross-references (when indices are parsed)
3. **Generate coverage report** indicating gaps and missing points

### Coverage Audit Script

`scripts/coverage_audit.py` (Wave 1) will:
```python
# Pseudocode
taxonomy = load_grammar_taxonomy('grammar/GRAMMAR_TAXONOMY.md')
bunpro_index = load_json('data/grammar-refs/bunpro_grammar_index.json')
jlpt_index = load_all_json('data/grammar-refs/jlpt-grammar/*.json')

gaps = bunpro_index['points'] - taxonomy['points']
missing_levels = taxonomy['points'] - jlpt_index['points']

write_report('coverage_report.md', gaps, missing_levels)
```

## Auto-Download vs Manual Curation

| Source | Auto-Download | Curation | Notes |
|--------|---------------|----------|-------|
| Bunpro | ❌ No | ✅ Yes | No official API; find community scrapes or manually visit bunpro.jp |
| Tofugu | ✅ Yes (HTML) | ⏳ Partial | HTML cached; extraction script needed |
| Imabi | ⚠️ Partial | ⏳ Partial | HTML fetch incomplete; JS rendering may help |
| JLPT grammar | ❌ No | ✅ Yes | GitHub sources unavailable; find alternatives |
| UniDic | ❌ No | ℹ️ Documented | User installs via `pip install unidic` |
| Yomitan dictionaries | ✅ Yes (catalog) | ✅ Optional | Catalog cached; learner-side install |

## Refresh Cadence

- **Quarterly** (recommended):
  - Re-fetch HTML caches (Tofugu, Imabi)
  - Check for new JLPT grammar repos
  - Monitor Yomitan catalog updates

- **Annually** (recommended):
  - Search for new Bunpro scrapes or alternatives
  - Review CC-100 corpus availability
  - Update UniDic documentation if major version released

## Licensing

When shipping content from these sources, respect the following:

- **Bunpro**: Proprietary; community scrapes fall under Bunpro ToS
- **Tofugu**: Proprietary; cache is for reference only
- **Imabi**: CC-BY-NC (non-commercial use; respect derivative work requirements)
- **JLPT**: Educational public domain (if/when available)
- **Yomitan**: MIT (catalog) + variable per dictionary (CC0, CC-BY, etc.)
- **UniDic**: CC-BY-SA-4.0
- **CC-100**: CC-BY-4.0 (per Common Crawl terms)

When attributing grammar points, always cite the original source and respect license requirements.

## Next Steps

1. **Populate `bunpro_grammar_index.json`**: Find and verify community scrape
2. **Parse Tofugu/Imabi**: Extract article/lesson structure from cached HTML
3. **Locate JLPT grammar lists**: Search GitHub for active maintained repos
4. **Run coverage_audit.py**: Generate initial gap report
5. **Add missing points**: Prioritize by JLPT level and frequency

---

**Last Updated**: 2026-05-16  
**Maintainer**: Grammar Reference Acquisition Script  
**MANIFEST**: See `MANIFEST.md` for detailed resource inventory
