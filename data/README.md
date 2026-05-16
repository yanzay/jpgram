# Data Directory

Central repository for all curated Japanese language learning data: lexical resources, linguistic references, and corpus metadata. This directory is **not version-controlled** (see `.gitignore`) but structured for easy refresh and distribution.

## Directory Structure

```
data/
├── README.md                    (this file)
├── .gitignore                   (entire data/ excluded from git)
│
├── dictionaries/                (~40–200 MB, varies)
│   ├── README.md               (dictionary sources & formats)
│   ├── MANIFEST.md             (inventory, licenses, SHA256)
│   ├── unidic-lite/            (morphological dict, ~40 MB)
│   ├── jmdict/                 (JMDict XML, ~100 MB)
│   └── mecab-ipadic/           (MeCab dictionary)
│
├── frequency-lists/            (~1–5 MB)
│   ├── README.md               (frequency source methodology)
│   ├── MANIFEST.md             (inventory)
│   ├── jlpt_vocab_by_level.json
│   ├── kanji_frequency.json
│   └── corpus_frequency.json
│
├── pitch-accent/               (~10–20 MB)
│   ├── README.md               (pitch accent sources & methodology)
│   ├── MANIFEST.md             (inventory)
│   ├── nhk_pitch_dict.json     (NHK pitch accent dictionary)
│   └── mora_patterns.json
│
├── grammar-refs/               (~428 KB)
│   ├── README.md               (grammar reference sources)
│   ├── MANIFEST.md             (inventory, refresh procedure)
│   ├── bunpro_grammar_index.json       (⚠️ placeholder)
│   ├── tofugu_grammar_toc.html         (✅ cached)
│   ├── tofugu_grammar_index.json       (📋 structure)
│   ├── imabi_toc.html                  (⚠️ incomplete)
│   ├── imabi_grammar_index.json        (📋 structure)
│   ├── jlpt-grammar/                   (❌ unavailable)
│   ├── UNIDIC_NOTES.txt
│   ├── CC100_NOTES.txt
│   └── (other documentation)
│
├── corpora/                    (metadata only, ~1 KB)
│   ├── README.md               (corpus references)
│   ├── MANIFEST.md             (inventory, download links)
│   └── cc100_ja_reference.txt  (URL & notes for CC-100 corpus)
│
└── readme-cache/               (~344 KB)
    ├── yomichan_dictionaries_index.html     (community dict catalog)
    └── learnjapanese_moe_yomichan.html      (setup guide)
```

## Subdirectory Overview

### `dictionaries/` (~40–200 MB)
**Purpose**: Morphological, semantic, and usage dictionaries for vocabulary/kanji lookup and linguistic processing.

**Key Resources**:
- **unidic-lite** (~40 MB): Morphological analyzer dictionary (shipped by default)
- **jmdict** (~100 MB): Japanese-multilingual dictionary (many frequency/kanji resources build on this)
- **mecab-ipadic**: MeCab dictionary (some tools depend on this)

**Consumed By**:
- `build_furigana.py` (kanji/kana conversion)
- `build_pitchaccent.py` (pitch lookup)
- Vocabulary list extraction scripts
- User-facing dictionary integrations (Yomitan, Anki)

**Refresh**: Yearly (or when major dictionary version releases)  
**License Compliance**: Multiple (CC0, CC-BY, CC-BY-SA); see `dictionaries/MANIFEST.md`

---

### `frequency-lists/` (~1–5 MB)
**Purpose**: Corpus-derived frequency rankings for vocabulary and kanji; used for content prioritization and learning sequencing.

**Key Resources**:
- **jlpt_vocab_by_level.json**: Vocabulary assignments per JLPT level (N1–N5)
- **kanji_frequency.json**: Kanji frequency from major corpora
- **corpus_frequency.json**: Raw frequency counts from aggregated corpus

**Consumed By**:
- Anki deck building (prioritize by frequency)
- Grammar point sequencing (frequency-weighted prerequisites)
- Coverage audits (identify high-frequency gaps)
- User-facing progress tracking

**Refresh**: Quarterly (recalculate from corpus if major content added)  
**License Compliance**: Various; depends on corpus source

---

### `pitch-accent/` (~10–20 MB)
**Purpose**: Pitch accent dictionary data (NHK standard) for generating audio and visual cues.

**Key Resources**:
- **nhk_pitch_dict.json**: NHK pitch accent dictionary (main resource)
- **mora_patterns.json**: Mora breakdown and pattern matching

**Consumed By**:
- `build_pitchaccent.py` (accent pattern lookup)
- Audio generation (pitch markup)
- User-facing pitch accent visualizations

**Refresh**: Yearly (or when NHK releases updated standard)  
**License Compliance**: CC-BY-SA (NHK resource)

---

### `grammar-refs/` (~428 KB)
**Purpose**: External grammar point indices and coverage references for gap detection and cross-validation.

**Key Resources**:
- **bunpro_grammar_index.json** (⚠️): Bunpro point list (awaiting community scrape)
- **tofugu_grammar_toc.html** (✅): Tofugu grammar guide table of contents (cached HTML)
- **imabi_toc.html** (⚠️): Imabi syllabus outline (incomplete; JS rendering may be needed)
- **jlpt-grammar/** (❌): JLPT level-specific grammar lists (GitHub sources unavailable)

**Consumed By**:
- `scripts/coverage_audit.py` (Wave 1): Gap detection
- `GRAMMAR_TAXONOMY.md` cross-reference validation
- User-facing "related grammar" suggestions

**Refresh**: Quarterly (re-fetch HTML; search for new repos)  
**License Compliance**: Proprietary (Bunpro, Tofugu) + CC-BY-NC (Imabi); cache for reference only

---

### `corpora/` (~1 KB metadata)
**Purpose**: Documentation and references for large corpora (no files downloaded due to size).

**Key Resources**:
- **CC-100 Japanese corpus**: ~15 GB (compressed), available at https://data.statmt.org/cc-100/ja.txt.xz
- **Tatoeba corpus**: Parallel corpus of sentences with translations
- **NAIST Japanese Corpus**: Annotated corpus for research

**Consumed By**:
- Language model training (optional, for users with compute)
- Frequency list generation (corpus statistics)
- Linguistic analysis (gap detection)

**Refresh**: Annually (verify URLs and sizes)  
**License Compliance**: CC-BY-4.0 (CC-100) + various per corpus

---

### `readme-cache/` (~344 KB)
**Purpose**: Cached HTML guides and catalogs for learner-facing recommendations.

**Key Resources**:
- **yomichan_dictionaries_index.html**: Community Yomitan dictionary catalog
- **learnjapanese_moe_yomichan.html**: Setup guide and dictionary recommendations

**Consumed By**:
- User documentation (learner setup guides)
- Dictionary integration recommendations

**Refresh**: Quarterly (monitor GitHub for catalog updates)

---

## Disk Footprint & Refresh Cadence

| Subdir | Typical Size | Refresh | Download Time | Automated |
|--------|--------------|---------|---------------|-----------|
| dictionaries/ | 40–200 MB | Yearly | ~30–60 min | Partial |
| frequency-lists/ | 1–5 MB | Quarterly | ~1 min | Yes |
| pitch-accent/ | 10–20 MB | Yearly | ~5 min | Yes |
| grammar-refs/ | 428 KB | Quarterly | <1 min | Partial |
| corpora/ | Metadata only | Yearly | N/A | No (user choice) |
| readme-cache/ | 344 KB | Quarterly | <1 min | Yes |
| **TOTAL** | **~50–230 MB** | **Quarterly (core)** | — | — |

**Notes**:
- Sizes exclude optional full dictionaries (jmdict, cc-100, unidic full)
- Most subdirectories can be auto-refreshed via scripts; see respective `README.md` files
- `dictionaries/` and `pitch-accent/` are the largest and most stable; can be cached/versioned per release
- `grammar-refs/` requires manual curation for Bunpro and JLPT sources; others can auto-refresh

---

## Git Ignore & Distribution

The entire `data/` directory is **excluded from version control** (see `.gitignore`):
```gitignore
# Exclude all data/ directory (managed separately)
/data/*
!/data/README.md
!/data/.gitignore
```

**Why?**
- Dictionaries, frequency lists, and corpora are large (50–230 MB)
- Licensing complexity (multiple CC-BY, proprietary, CC-BY-NC sources)
- Frequent updates (quarterly refresh cadence) without code changes
- User may selectively download subsets for their use case

**Distribution Strategy**:
1. **Core build**: Bundle `dictionaries/` + `frequency-lists/` + `pitch-accent/` (cached in CI/CD)
2. **Optional references**: Users clone `grammar-refs/` separately for audit/curation
3. **Learner guides**: Ship `readme-cache/` HTML files in user-facing docs

---

## Workflow: Adding/Updating Resources

### Scenario 1: Add a new grammar reference (e.g., Genki textbook index)

1. Create `grammar-refs/genki_grammar_index.json` with structure:
   ```json
   {
     "source": "https://www.genki.jp/",
     "license": "Proprietary",
     "entries": [...]
   }
   ```
2. Add to `grammar-refs/MANIFEST.md` with date, size, and SHA256
3. Update `grammar-refs/README.md` with description
4. Run `scripts/coverage_audit.py` to cross-check against taxonomy

### Scenario 2: Refresh frequency lists

1. Re-run frequency extraction script (or source from JLPT official lists)
2. Update `frequency-lists/*.json` with new counts
3. Update SHA256 and date in `frequency-lists/MANIFEST.md`
4. Update `frequency-lists/README.md` with recalc methodology

### Scenario 3: User requests new dictionary

1. Download to `dictionaries/` (or note download procedure in `UNIDIC_NOTES.txt` style)
2. Add to `dictionaries/MANIFEST.md`
3. Update `build_furigana.py` or other scripts if new dict is consumed
4. Test with `validate_anki_data.py` to ensure consistency

---

## License Compliance Summary

When distributing jpgram, ensure:

| Subdir | Primary Licenses | Compliance Notes |
|--------|------------------|------------------|
| dictionaries/ | CC-BY-SA, CC0, CC-BY | Ship manifests; cite sources in output |
| frequency-lists/ | Various | Cite source corpus in list metadata |
| pitch-accent/ | CC-BY-SA | Cite NHK as source |
| grammar-refs/ | Proprietary + CC-BY-NC | Cache for reference; do not redistribute |
| corpora/ | CC-BY-4.0, various | Metadata only; user responsible for corpus download |
| readme-cache/ | MIT, CC-BY, various | Ship HTML; cite original source |

When packaging for users:
- Include `MANIFEST.md` from each subdir
- Add license summary to main README
- Link to source projects for attribution
- Respect non-commercial (CC-BY-NC) restrictions if Imabi content is used

---

## Next Steps

1. **Populate `grammar-refs/`**: Complete bunpro and JLPT indices (see `grammar-refs/README.md`)
2. **Extract frequency stats**: Build `frequency-lists/` from JLPT corpus
3. **Validate dictionaries**: Ensure `dictionaries/` index is complete
4. **Run coverage audit**: Execute `scripts/coverage_audit.py` to identify gaps
5. **Create refresh schedule**: Document quarterly/yearly cron jobs

---

**Last Updated**: 2026-05-16  
**Maintainers**: Grammar Reference & Data Pipeline  
**Total Tracked Resources**: 25+  
**Version**: 1.0 (initial acquisition)
