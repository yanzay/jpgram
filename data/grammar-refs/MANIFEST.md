# Grammar References Manifest

**Date**: 2026-05-16  
**Total Size (downloaded)**: ~428 KB  
**Update Cadence**: Quarterly (manual refresh recommended)

## Resources Acquired

| Resource | Source | Type | Size | SHA256 | License | Status | Notes |
|----------|--------|------|------|--------|---------|--------|-------|
| bunpro_grammar_index.json | https://bunpro.jp/grammar_points | JSON (placeholder) | 465 B | N/A | Proprietary | ⚠️ Manual curation | No official API; community exports may be found at https://github.com/Heliozoa/bunpro-deconjugator |
| tofugu_grammar_toc.html | https://www.tofugu.com/japanese-grammar/ | HTML cache | 77.6 KB | — | Proprietary | ✅ Downloaded | Full Tofugu grammar guide TOC; parsing ready |
| tofugu_grammar_index.json | https://www.tofugu.com/japanese-grammar/ | JSON (structure) | 176 B | N/A | Proprietary | 📋 Ready for parsing | Generated structure awaiting manual article extraction |
| imabi_toc.html | https://www.imabi.org/syllabus | HTML cache | 162 B | N/A | CC-BY-NC | ⚠️ Incomplete fetch | Site returns minimal HTML; may require JavaScript rendering |
| imabi_grammar_index.json | https://www.imabi.org/ | JSON (structure) | 174 B | N/A | CC-BY-NC | 📋 Ready for parsing | Placeholder structure for lesson extraction |
| jlpt-grammar/ | GitHub (Tanos, Daniel-Tang) | Directory | — | — | N/A | ❌ Not found | Both repos return 404; may have been removed or archived |
| UNIDIC_NOTES.txt | https://clrd.ninjal.ac.jp/unidic/ | Documentation | 388 B | N/A | CC-BY-SA-4.0 | ℹ️ Documented | Full UniDic (~2 GB) not auto-downloaded; user install via `pip install unidic` |
| yomichan_dictionaries_index.html | https://github.com/MarvNC/YomichanDictionaries | HTML index | 299 KB | — | MIT | ✅ Downloaded | Community Yomitan dictionary catalog; learner-side recommendation |
| learnjapanese_moe_yomichan.html | https://learnjapanese.moe/yomichan/ | HTML guide | 42.5 KB | — | Various | ✅ Downloaded | Setup guide and recommendations for Yomitan dictionaries |
| CC100_NOTES.txt | https://data.statmt.org/cc-100/ja.txt.xz | Documentation | 478 B | N/A | CC-BY-4.0 | ℹ️ Documented | CC-100 Japanese corpus (~15 GB compressed); not auto-downloaded |

## Download Summary

**Successfully Downloaded**:
- ✅ Tofugu grammar TOC + structure (77.6 KB)
- ✅ Yomitan dictionaries index (299 KB)
- ✅ Learn Japanese guide (42.5 KB)

**Partially Available**:
- 📋 Imabi structure (requires JS rendering or manual fetch)
- 📋 Tofugu parsing (HTML cached, needs extraction script)

**Manual Curation Needed**:
- ⚠️ Bunpro (no official API; community sources only)
- ❌ JLPT grammar repos (both GitHub sources return 404)

**Documented but Not Downloaded**:
- ℹ️ UniDic full dictionary (user installs via pip)
- ℹ️ CC-100 corpus (too large; reference only)

## Refresh Procedure

1. **JLPT Grammar Lists**: Search GitHub for new `jlpt-grammar-*` or `tanos-*` repos; verify formats
2. **Bunpro**: Check https://github.com/Heliozoa/bunpro-deconjugator and related projects for scrape updates
3. **Tofugu/Imabi**: Re-fetch HTML quarterly; may need browser-based scraping if JS-rendered
4. **Yomitan**: Monitor https://github.com/MarvNC/YomichanDictionaries for catalog updates
5. **CC-100**: Verify URL at https://data.statmt.org/cc-100/ remains stable

## Cross-Reference with GRAMMAR_TAXONOMY.md

The `scripts/coverage_audit.py` (Wave 1) will:
1. Read shipped grammar points from `grammar/GRAMMAR_TAXONOMY.md`
2. Compare against `bunpro_grammar_index.json` (when populated)
3. Compare against `jlpt-grammar/*.json` (when available)
4. Report missing points and gaps

Expected workflow:
```
grammar/GRAMMAR_TAXONOMY.md
  └─> scripts/coverage_audit.py
      └─> data/grammar-refs/{bunpro,jlpt-grammar,tofugu,imabi}_*.json
          └─> coverage_report.md (gaps, priorities)
```

## Licensing Notes

- **Bunpro**: Proprietary (community-scraped)
- **Tofugu**: Proprietary; HTML cache for reference only
- **Imabi**: CC-BY-NC (non-commercial use)
- **JLPT**: Educational/public domain (where available)
- **Yomitan**: MIT (catalog) + variable per dictionary
- **UniDic**: CC-BY-SA-4.0
- **CC-100**: CC-BY-4.0

---

**Last Updated**: 2026-05-16  
**Next Review**: Q3 2026
