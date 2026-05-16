# Frequency Lists & Corpus Statistics Manifest

**Date Generated:** 2026-05-16  
**Total Files:** 9  
**Total Size:** ~1.65 MB

## JLPT Vocabulary Lists (N5-N1)

| File | Level | Size | Entries | SHA256 | License | Source |
|------|-------|------|---------|--------|---------|--------|
| jlpt/n5.csv | N5 | 63,965 B | ~718 | `f89abc86...` | CC BY-SA 3.0 | open-anki-jlpt-decks |
| jlpt/n4.csv | N4 | 49,627 B | ~668 | `0e835f40...` | CC BY-SA 3.0 | open-anki-jlpt-decks |
| jlpt/n3.csv | N3 | 167,423 B | ~2,141 | `ba071571...` | CC BY-SA 3.0 | open-anki-jlpt-decks |
| jlpt/n2.csv | N2 | 135,869 B | ~1,907 | `2d0f1ddd...` | CC BY-SA 3.0 | open-anki-jlpt-decks |
| jlpt/n1.csv | N1 | 191,444 B | ~2,699 | `12091163...` | CC BY-SA 3.0 | open-anki-jlpt-decks |

**Format:** CSV (word,reading,definition,tags,id)  
**Source:** https://github.com/jamsinclair/open-anki-jlpt-decks  
**Status:** ✅ All 5 levels successfully downloaded and validated

## Kanji Frequency Lists (Multiple Corpora)

| File | Corpus | Size | Entries | SHA256 | License | Source |
|------|--------|------|---------|--------|---------|--------|
| kanji_wikipedia_frequency.json | Wikipedia | 702,143 B | 20,933 | `322c3306...` | MIT | scriptin/topokanji |
| kanji_aozora_frequency.json | Aozora (Fiction) | 221,829 B | 6,118 | `900f85f8...` | MIT | scriptin/topokanji |
| kanji_twitter_frequency.json | Twitter | 158,445 B | 4,517 | `3d94af9b...` | MIT | scriptin/topokanji |
| kanji_news_frequency.json | News | 128,594 B | 3,640 | `78b841a5...` | MIT | scriptin/topokanji |

**Format:** JSON (array of objects with character, rank, frequency, etc.)  
**Source:** https://github.com/scriptin/kanji-frequency  
**Status:** ✅ 4 corpora successfully downloaded and validated

## Detailed File Information

### JLPT Vocabulary Lists
- **CSV Format:** word,reading,meaning,tags,id_hash
- **Rows per file:** 718 (N5) to 2,699 (N1)
- **Usage:** Feed into tagging pipeline for `jlpt:n5`, `jlpt:n4`, etc. tags
- **License:** CC BY-SA 3.0 (open-anki-jlpt-decks)

### Kanji Frequency Lists
- **JSON Format:** Array of objects: `{character, rank, frequency, documents, datasets}`
- **Coverage:** ~3,600-20,900 unique kanji per corpus
- **License:** MIT (scriptin/topokanji)
- **Recommended Usage:**
  - `wikipedia`: General, formal Japanese (best for deck building)
  - `aozora`: Literary/fiction texts (classic literature)
  - `news`: News/journalism content
  - `twitter`: Social media/colloquial Japanese

## Download Status Summary

| Category | Status | Details |
|----------|--------|---------|
| JLPT Vocab | ✅ SUCCESS | All 5 levels (2,698 total words) |
| Kanji Frequency | ✅ SUCCESS | 4 corpora (multi-source analysis) |
| BCCWJ Short Units | ⚠️ INCOMPLETE | Primary source requires auth; fallback sources 404'd |
| Anime/Netflix Freq | ⚠️ NOT FOUND | jpdb.io sources unavailable |
| Tanos JLPT Lists | ⚠️ NOT FOUND | HTML-only (would require scraping) |
| Tatoeba Corpus | ⏭️ SKIP | Handled by dictionaries agent |

## Failed/Skipped Sources & Reasons

1. **BCCWJ Short Units (NINJAL)** - Primary repository requires authentication
2. **BCCWJ Mirror (scriptin/topokanji)** - Path incorrect in current repo state
3. **AnimeFrequency (kanjieater)** - Repository archived or moved
4. **Wikipedia Yomitan** (MarvNC) - Path not found
5. **JLPT Word Lists** (elzup) - Repository structure changed
6. **University of Leeds Corpus** - Direct access unavailable
7. **Kanji Frequency** (scriptin/kanji-frequency main data.json) - Source structure changed
8. **Kanjium SQLite** - File redirect issue
9. **Tanos JLPT** - HTML format only (no direct download)
10. **Tatoeba JP Corpus** - Being handled separately by dictionaries agent

## Notes for Refresh & Maintenance

- JLPT lists are actively maintained in open-anki-jlpt-decks repo
- Kanji frequency lists are refreshed periodically in scriptin/topokanji
- To re-download: Use the source URLs listed above with curl/wget
- SHA256 checksums provided for integrity verification
- Recommend monthly refresh of both JLPT and kanji frequency data
