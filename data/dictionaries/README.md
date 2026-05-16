# Dictionary Resources

This directory contains Japanese language reference data consumed by the jpgram build pipeline.

## Files

- **JMdict_e.gz** — Primary Japanese↔English dictionary (EDRDG). Gzipped XML containing ~180k word entries with readings, definitions, and example sentences. Consumed by `build_furigana.py` for word lookup and furigana generation.

- **JMnedict.xml.gz** — Proper name dictionary (EDRDG). Gzipped XML with ~750k proper names (persons, places, organizations). Used for name kanji reading resolution.

- **kanjidic2.xml.gz** — Comprehensive kanji database (EDRDG). Contains stroke counts, on/kun readings, meanings, JLPT levels, radical assignments for all ~13k kanji. Reserved for future `build_kanji.py` pipeline stage.

- **radkfile.gz** — Radical-to-kanji index. Maps each of ~200 radicals to all kanji containing that radical. Supports kanji decomposition and component analysis.

- **kradfile.gz** — Kanji-to-radical decomposition. Reverse mapping: each kanji to its constituent radicals. Enables stroke-based and radical-based kanji learning workflows.

- **jpn_sentences.tsv.bz2** — Tatoeba Japanese sentence corpus (CC0 public domain). Tab-separated format: sentence_id | language_code | text. ~160k JP sentences. Useful for example-sentence selection and frequency analysis in build_furigana.py and future stages.

## Pipeline Integration

- **build_furigana.py** — Reads JMdict_e.gz to generate furigana annotations and fetch definitions.
- **build_pitchaccent.py** — May reference JMdict_e.gz for pitch accent assignment to words.
- **build_kanji.py** (future) — Will consume kanjidic2.xml.gz, radkfile.gz, kradfile.gz for kanji metadata and stroke data.

## Licensing

All EDRDG resources (JMdict, JMnedict, KANJIDIC2, radkfile, kradfile) are distributed under **CC BY-SA 4.0**. 

Tatoeba data is **CC0 (public domain)** — no attribution required.

These files are **excluded from git** via `.gitignore`'s `data/` rule, meaning they are learner-side only and will not be committed to the repository. This is by design: the build pipeline expects them to be present locally, and their size (~30 MB compressed) makes them unsuitable for version control.

## Refresh Instructions

To refresh these resources to newer versions:

```bash
cd data/dictionaries
# Remove old files
rm -f JMdict_e.gz JMnedict.xml.gz kanjidic2.xml.gz radkfile.gz kradfile.gz jpn_sentences.tsv.bz2
# Re-run the download script (e.g., from CI or manually)
# Update MANIFEST.md with new dates and hashes
```

All URLs are stable (EDRDG hosts have been consistent for 15+ years; Tatoeba exports are refreshed weekly).
