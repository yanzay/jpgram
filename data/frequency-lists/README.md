# Japanese Frequency Lists & Corpus Statistics

**Purpose:** Provide frequency data for deck building, word prioritization, and tagging in the jpgram Japanese language learning deck.

**Last Updated:** 2026-05-16  
**Data Sources:** 2 primary sources (JLPT, Kanji Frequency)  
**Total Coverage:** 2,698 JLPT words + 20,933 kanji variants

---

## 📊 Available Data

### 1. JLPT Vocabulary Lists (N5-N1)

**Files:** `jlpt/n5.csv`, `jlpt/n4.csv`, `jlpt/n3.csv`, `jlpt/n2.csv`, `jlpt/n1.csv`

**Format:** CSV with columns:
```
word,reading,meaning,tags,id_hash
```

**Example:**
```csv
日本,にほん,Japan,JLPT JLPT_5 geography,abc123def456
漢字,かんじ,kanji; Chinese characters,JLPT JLPT_2 kanji,xyz789uvw012
```

**Statistics:**
- **N5 (Beginner):** 718 words
- **N4 (Upper Beginner):** 668 words  
- **N3 (Intermediate):** 2,141 words
- **N2 (Upper Intermediate):** 1,907 words
- **N1 (Advanced):** 2,699 words
- **Total:** 8,133 unique JLPT vocabulary entries

**License:** CC BY-SA 3.0  
**Source:** https://github.com/jamsinclair/open-anki-jlpt-decks

**Usage in Pipeline:** See [Frequency Tagging](#frequency-tagging) below.

---

### 2. Kanji Frequency Lists (Multi-Source)

**Files:** 
- `kanji_wikipedia_frequency.json` (20,933 entries)
- `kanji_aozora_frequency.json` (6,118 entries)
- `kanji_twitter_frequency.json` (4,517 entries)
- `kanji_news_frequency.json` (3,640 entries)

**Format:** JSON array of objects
```json
[
  {
    "character": "日",
    "rank": 1,
    "frequency": 49280,
    "documents": 95000,
    "datasets": {
      "aozora": {"rank": 8, "frequency": 12345},
      "news": {"rank": 5, "frequency": 8901},
      "twitter": {"rank": 2, "frequency": 15678},
      "wikipedia": {"rank": 1, "frequency": 49280}
    }
  },
  ...
]
```

**Corpus Characteristics:**

| Corpus | Best For | Characteristics | Size |
|--------|----------|-----------------|------|
| **Wikipedia** | General, formal JP | Encyclopedic content, modern standard Japanese | 20,933 kanji |
| **Aozora** | Literary texts | Classic/contemporary fiction, public domain | 6,118 kanji |
| **News** | Journalism | News articles, formal register | 3,640 kanji |
| **Twitter** | Social media | Colloquial, contemporary usage | 4,517 kanji |

**License:** MIT  
**Source:** https://github.com/scriptin/kanji-frequency

**Usage in Pipeline:** See [Frequency Tagging](#frequency-tagging) and [Domain Tagging](#domain-tagging) below.

---

## 🏷️ Tagging Pipeline

This section describes how frequency data feeds into the `apply_taxonomy_tags.py` script (or equivalent).

### Frequency Tagging

**Frequency tags** are applied based on **cumulative word frequency rankings**:

```
frequency:top1k    → Rank 1-1,000 most common words
frequency:top5k    → Rank 1,001-5,000
frequency:top10k   → Rank 5,001-10,000  
frequency:low      → Rank 10,001+
```

**Algorithm:**

1. **Aggregate all frequency sources** (currently: Wikipedia kanji frequency)
2. **Create combined ranking** by:
   - Normalizing each corpus's frequency scores (0-1)
   - Computing weighted average across corpora (weights TBD)
   - Sorting by combined score
3. **Apply tags** to deck entries:
   ```python
   if rank <= 1000:
       tags.append("frequency:top1k")
   elif rank <= 5000:
       tags.append("frequency:top5k")
   elif rank <= 10000:
       tags.append("frequency:top10k")
   else:
       tags.append("frequency:low")
   ```

**Current Status:** ⚠️ Implementation pending. Frequency scores need to be:
- Normalized across multiple sources
- Weighted by corpus relevance to deck goals
- Tested against known frequency lists (e.g., 2000 most common words)

**Example Output:**
```
Word: 日本 (Nihon - Japan)
Tags: jlpt:n5, frequency:top1k, location, geography
Justification: Rank ~50 in Wikipedia corpus
```

### JLPT Level Tagging

**JLPT tags** are deterministic—words in each CSV file receive their corresponding tag:

```python
for jlpt_level in ["n5", "n4", "n3", "n2", "n1"]:
    with open(f"jlpt/{jlpt_level}.csv") as f:
        reader = csv.DictReader(f)
        for row in reader:
            word = row["word"]
            entry = deck[word]  # Find in deck
            entry.tags.add(f"jlpt:{jlpt_level}")
```

**Applied Tags:** `jlpt:n5`, `jlpt:n4`, `jlpt:n3`, `jlpt:n2`, `jlpt:n1`

**Important Notes:**
- A word may appear in multiple JLPT lists (e.g., 実は in n3.csv and n2.csv)
- All applicable tags should be added (not mutually exclusive)
- JLPT lists are **normative** (official test vocabulary) vs frequency (descriptive)

---

### Domain Tagging (Future)

Once anime/Netflix/drama frequency lists are acquired, they will enable:

```
domain:anime-manga      → Top words in anime subtitles
domain:netflix          → Top words in Netflix Japanese content
domain:drama            → Top words in Japanese TV dramas
```

**Algorithm (placeholder):**
```python
if word_rank_in_anime <= 1000:
    tags.append("domain:anime-manga")
if word_rank_in_netflix <= 1000:
    tags.append("domain:netflix")
```

**Status:** 📍 Waiting for:
1. jpdb.io frequency list access
2. Open anime subtitle corpus (e.g., ASENINE)
3. Alternative: manual curation from popular anime/drama scripts

---

## 📥 Data Acquisition & Refresh

### How to Download/Update

**Quick Refresh (Bash):**
```bash
cd data/frequency-lists

# JLPT Lists
for level in n5 n4 n3 n2 n1; do
  curl -L -o jlpt/${level}.csv \
    "https://raw.githubusercontent.com/jamsinclair/open-anki-jlpt-decks/main/src/${level}.csv"
done

# Kanji Frequency (Wikipedia corpus recommended)
curl -L -o kanji_wikipedia_frequency.json \
  "https://raw.githubusercontent.com/scriptin/topokanji/master/data/kanji-frequency/wikipedia.json"

# Optional: Other corpora
for corpus in aozora news twitter; do
  curl -L -o kanji_${corpus}_frequency.json \
    "https://raw.githubusercontent.com/scriptin/topokanji/master/data/kanji-frequency/${corpus}.json"
done
```

**Validation:**
```bash
# Verify JLPT CSVs are valid
python3 -c "import csv,glob; [csv.DictReader(open(f)).fieldnames for f in glob.glob('jlpt/*.csv')]"

# Verify Kanji JSONs are valid
python3 -c "import json,glob; [json.load(open(f)) for f in glob.glob('kanji_*.json')]"

# Check SHA256 (see MANIFEST.md for expected values)
sha256sum jlpt/*.csv kanji_*.json
```

### Recommended Refresh Schedule

| Source | Frequency | Reason |
|--------|-----------|--------|
| JLPT Lists | Monthly | Updated periodically with test changes |
| Kanji Frequency | Quarterly | Corpus data updates in scriptin repos |
| Domain Lists (Anime/Netflix) | As available | No stable source yet |

### Failed Sources & Why

**BCCWJ Short Units** (Balanced Corpus of Contemporary Written Japanese)
- ❌ Primary: NINJAL repository requires authentication
- ❌ Mirror: topokanji path changed; repo no longer hosts this data
- **Impact:** High-quality corpus frequency data unavailable. Workaround: Use Wikipedia frequency as proxy.

**Anime/Netflix Frequency Lists**
- ❌ jpdb.io: No public API; dictionary format incompatible
- ❌ kanjieater/AnimeFrequency: Repository archived
- ❌ themoeway/jp-mining-note: Yomitan dictionary format (not frequency list)
- **Impact:** Cannot tag words by anime/drama frequency yet. Manual curation needed.

**Tanos JLPT Lists**
- ❌ HTML-only (no machine-readable download)
- ✅ Alternative: jamsinclair/open-anki-jlpt-decks (CSV, more complete)

**Alternative BCCWJ Sources Investigated**
- Terry Joyce's BCCWJ compilation: Access restricted
- NatsumeRyo's BCCWJ fork: Outdated or removed
- **Recommendation:** If high-quality BCCWJ frequency needed, purchase BCCWJ DVD or request researcher access

---

## 📋 Licensing

| Source | License | Attribution Required? | Commercial Use? |
|--------|---------|:----------------------:|:----------------:|
| JLPT Lists (jamsinclair) | CC BY-SA 3.0 | Yes | Yes (with conditions) |
| Kanji Frequency (scriptin) | MIT | Yes | Yes |
| NINJAL BCCWJ | CC BY 4.0* | Yes | Yes |
| Tanos Lists | — | — | No (direct use) |
| Tatoeba | CC BY 2.0 | Yes | Yes (with conditions) |

*BCCWJ official license; not yet acquired in this project.

**jpgram Attribution:**
When using this deck with these frequency lists, attribution example:
```
Frequency data sourced from:
- JLPT vocabulary: open-anki-jlpt-decks (CC BY-SA 3.0)
- Kanji frequency: scriptin/kanji-frequency (MIT)
```

---

## 🛠️ Integration Points

### Where These Lists Are Used

1. **`apply_taxonomy_tags.py`**
   - Reads frequency rankings
   - Applies `frequency:*` and `domain:*` tags
   - Matches words/kanji to deck entries

2. **Deck Building (`build_deck.py`)**
   - Uses JLPT tags for curriculum ordering
   - Uses frequency tags for priority flagging
   - Uses domain tags for content filtering

3. **Dashboard/Stats**
   - Distribution charts: "% of deck in top 1k words"
   - JLPT level breakdown: "X words at N5, Y at N4, ..."
   - Corpus comparison: Show coverage across multiple sources

---

## 🐛 Known Issues & TODOs

- [ ] **BCCWJ Frequency:** Primary source restricted; consider scraping NINJAL-LWP web interface
- [ ] **Anime/Netflix Frequency:** No stable open source found; manual curation or request jpdb.io access
- [ ] **Frequency Normalization:** Algorithm for combining multiple corpus rankings not yet specified
- [ ] **Tanos JLPT Lists:** HTML scraping not implemented; current jamsinclair CSVs adequate for MVP
- [ ] **Kanji-Word Linking:** Need script to infer word frequency from constituent kanji
- [ ] **Frequency Tiers:** Exact thresholds (1k, 5k, 10k) TBD; currently placeholder values

---

## 📚 References & Further Reading

- **BCCWJ:** https://clrd.ninjal.ac.jp/bccwj/en/
- **scriptin/kanji-frequency:** https://github.com/scriptin/kanji-frequency
- **scriptin/topokanji:** https://github.com/scriptin/topokanji
- **open-anki-jlpt-decks:** https://github.com/jamsinclair/open-anki-jlpt-decks
- **JLPT Official Info:** https://www.jlpt.jp/
- **Yomichan/Yomitan:** https://github.com/FooSoft/yomichan (uses frequency dicts like these)

---

## 💬 Questions?

See the parent `data/README.md` or contact the deck maintainer.

**Last Updated:** 2026-05-16  
**Status:** ✅ MVP (core JLPT + kanji frequency working; domain tagging pending)
