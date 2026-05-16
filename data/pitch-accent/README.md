# Japanese Pitch-Accent Data

This directory contains pre-built pitch-accent databases for the jpgram learner deck, consumed by `build_pitchaccent.py`.

## Tokyo Pitch-Accent Notation

Japanese pitch accent describes the melodic contour of a word using **mora-by-mora pitch levels**:

### Accent Types

| Type | Pattern | Example | Notation |
|------|---------|---------|----------|
| **Heiban** (平板) | `LHHH…` (pitch rises after first mora, stays high) | 学生 (がくせい) | **0** |
| **Atamadaka** (頭高) | `HLLL…` (pitch drops after first mora, stays low) | 橋 (はし) | **1** |
| **Nakadaka** (中高) | `LHHL…` (rises, then drops at N-th mora) | 先生 (せんせい, drops at 3rd) | **3** |
| **Odaka** (尾高) | `LHH…L` (rises, drops at final mora) | 色 (いろ, drops at 3rd) | **2** |

**Pitch Height Contour:**
- **L** = Low pitch
- **H** = High pitch

Example: 先生 (せんせい) with accent=3 → `LHHL` → pitch rises from せ → ん, then drops on せい

### Mora Counting Rules

- Each kana character = 1 mora (e.g., あ い う え お = 1 mora each)
- Small yō-on (ゃ ゅ ょ) attaches to previous mora, not counted separately (e.g., きゃ = 1 mora)
- Long vowels (～う for o-sound, ～ー for foreign words) = 1 mora each
- Geminate consonant (っ) = 1 mora

Example mora counts:
- 学生 (がくせい) = が・く・せ・い = 4 moras
- 学校 (がっこう) = が・っ・こ・う = 4 moras
- 家 (いえ) = い・え = 2 moras

## Data Source Priority & Fallback Chain

The `build_pitchaccent.py` script looks up each word token in this order:

1. **`data/accents.sqlite`** (Kanjium pitch-accent SQLite)
   - **Canonical source** for jpgram
   - ~107k entries with verified pitch patterns
   - O(1) lookup by expression
   - Built from `data/pitch-accent/accents.txt` on 2026-05-16
   - **License:** MIT

2. **`data/nhk_accents.csv`** (NHK Pronunciation Dictionary)
   - Fallback if token not in Kanjium
   - Large CSV from NHK broadcast standards
   - ~14 MB uncompressed
   - Contains pitch accent info in column layout
   - **License:** MIT

3. **`data/wadoku_accents.tsv`** (Wadoku German-Japanese dictionary)
   - Not currently staged (no public release found)
   - Would be used if JmdictFurigana becomes available

**First match wins:** A word that appears in both Kanjium and NHK will use the Kanjium entry.

## How to Refresh the Data

### Download Latest Sources

```bash
# Kanjium accents.txt (3.1 MB)
curl -L -o data/pitch-accent/accents.txt \
  "https://raw.githubusercontent.com/mifunetoshiro/kanjium/master/data/source_files/raw/accents.txt"

# NHK pronunciation (14 MB)
git clone https://github.com/javdejong/nhk-pronunciation.git /tmp/nhk-pronunciation
cp /tmp/nhk-pronunciation/ACCDB_unicode.csv data/pitch-accent/nhk_accents.csv
```

### Rebuild SQLite Index

```bash
python3 << 'PYTHON'
import sqlite3
from pathlib import Path

text_file = Path("data/pitch-accent/accents.txt")
db_file = Path("data/pitch-accent/accents.sqlite")

con = sqlite3.connect(db_file)
cur = con.cursor()
cur.execute("DROP TABLE IF EXISTS accents")
cur.execute("""
    CREATE TABLE accents (
        id INTEGER PRIMARY KEY,
        expression TEXT NOT NULL,
        reading TEXT NOT NULL,
        accent INTEGER NOT NULL
    )
""")
cur.execute("CREATE INDEX idx_expression ON accents(expression)")

count = 0
with open(text_file, encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = line.split('\t')
        if len(parts) >= 3:
            try:
                cur.execute(
                    "INSERT INTO accents (expression, reading, accent) VALUES (?, ?, ?)",
                    (parts[0], parts[1], int(parts[2]))
                )
                count += 1
            except (ValueError, IndexError):
                pass

con.commit()
con.close()
print(f"✓ Rebuilt {db_file}: {count} entries")
PYTHON
```

### Symlink for build_pitchaccent.py

```bash
ln -sf pitch-accent/accents.sqlite data/accents.sqlite
```

## License & Attribution

| Source | License | Notes |
|--------|---------|-------|
| Kanjium | MIT | https://github.com/mifunetoshiro/kanjium |
| NHK Pronunciation | MIT | https://github.com/javdejong/nhk-pronunciation |

All files in this directory are freely redistributable under these permissive licenses. No proprietary data is included.

## Example: How Pitch Accent Surfaces on Cards

The jpgram card layout (Wave 1) uses the pitch-accent index as follows:

**Front (Hiragana Practice):**
```
学生 ← blank field, learner fills in reading
```

**Back (with pitch overlay):**
```
Reading: がくせい
Accent:  0 (Heiban) — pitch contour: LHHH ───────
                      ┌──────────────
                    ┌─┘

Card hint: "This word has no pitch drop (heiban);
           keep pitch HIGH after the first mora."
```

**Study Flow:**
1. Learner reads the kanji (学生)
2. Learns the reading (がくせい) from back
3. **Also learns the pitch pattern** (0 = LHHH = no drop)
4. Over time, develops native-like pitch intuition

This integration helps learners **produce** natural-sounding Japanese, not just understand it.

---

**Last Updated:** 2026-05-16  
**Total Data:** ~25.7 MB (accents.sqlite + nhk_accents.csv)  
**Tokens in Kanjium:** 106,925
