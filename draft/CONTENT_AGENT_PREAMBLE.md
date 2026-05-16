# Content-generator subagent preamble

This document is the SHARED contract every Wave 3+ content subagent must
follow. Read it once, then act on your slice-specific task.

## File-write contract (a previous agent class failed all of these)

* Use absolute paths: `pathlib.Path('/Users/ograchov/projects/jpgram/grammar/<module>/<filename>')`.
* Write with `.write_text(content, encoding='utf-8')`.
* After each write, `print(p.stat().st_size, p)` to confirm the file is on disk.
* Do NOT use `csv.writer` for TSV output — it quotes tabs. Use
  `'\t'.join(row) + '\n'`.

## Note-type schemas (exact column order)

```
Recognition:  JP\tReading\tEN\tLabel\tFormula\tMainUse\tQuickCue\tContrast\tAudio\tTags   (10)
Production:   Prompt\tTarget\tReading\tSample\tWhy\tAudio\tTags                            (7)
Cloze:        Text\tReading\tHint\tAudio\tTags                                             (5)
Contrast:     JP\tOptionA\tOptionB\tAnswer\tWhy\tTip\tAudio\tTags                          (8)
```

Tags column = empty string. apply_taxonomy_tags.py fills it from path.

## Required file headers (exactly these lines, in this order)

```
#separator:tab
#html:true
#columns:<schema-here>
#notetype:<Recognition|Production|Cloze|Contrast>
#deck:Japanese Grammar::<MODULE NAME>::<TYPE>
```

Deck path examples:
* `Japanese Grammar::02 - N4 Grammar::Recognition`
* `Japanese Grammar::06 - Keigo::Contrast`

## Audio HASH (source convention by note type)

```python
import hashlib, re
CLOZE = re.compile(r'\{\{c\d+::([^:}]+)(?:::[^}]+)?\}\}')

def audio_hash(jp): return hashlib.sha1(jp.strip().encode('utf-8')).hexdigest()[:12]

# Recognition:   hash JP column (row[0])
# Production:    hash Sample column (NOT Prompt)
# Cloze:         hash CLOZE.sub(r'\1', row[0])  # strip cloze markup first
# Contrast:      hash row[0].replace('___', row[3])  # substitute Answer into ___
#                EXCEPT when the contrast is a sense-discrimination drill
#                (no '___' in JP) — then hash JP as-is.
```

Then `audio_field = f"[sound:{audio_hash(...)}.mp3]"`

## Reading column (HARD requirement)

* Must contain ZERO kanji and ZERO ASCII digits.
* Generate via pykakasi:
  ```python
  import pykakasi
  kks = pykakasi.kakasi()
  reading = ''.join(c.get('hira') or c.get('orig','') for c in kks.convert(jp))
  assert not any('\u4e00' <= ch <= '\u9fff' for ch in reading), reading
  assert not any(ch.isdigit() for ch in reading), reading
  ```
* For sentences with numbers, manually substitute the hiragana form BEFORE
  feeding pykakasi (e.g. `'1時' → 'いちじ'`, `'2026年' → 'にせんにじゅうろくねん'`).
* For cloze rows, the Reading column wraps the kana of the answer with the
  same `{{c1::...}}` markup. Compute: render reading of the FULL resolved
  JP, then re-wrap the answer's kana.

## Content quality bar

* Every JP sentence ≤ 25 morae, natural modern Japanese.
* Every Reading column kana-only as described above.
* Every English (`EN` / `Why` / `Hint` / `Sample`) field is a clean
  one-sentence gloss. DO NOT append `(English translation in parens)` to
  any JP field — TTS will speak it aloud.
* Use `ください` (kana) consistently, not `下さい` (kanji form), unless
  intentionally drilling kanji-form keigo.
* Cross-check uncommon vocabulary against `data/dictionaries/JMdict_e.gz`.
* Pitch-accent words must exist in `data/accents.sqlite`.

## Uniqueness

* No duplicate JP sentences WITHIN your slice.
* No duplicates ACROSS your slice and any TSV already on disk in
  `grammar/00-foundation/` or `grammar/01-n5/` (Wave 1+2 ship).
* For new waves, also avoid duplicates with concurrent sibling slices
  (your task description will list them).

To check, before writing:
```python
existing = set()
import csv, re
for f in Path('grammar').rglob('*.tsv'):
    for ln in f.read_text(encoding='utf-8').splitlines():
        if ln.startswith('#') or not ln.strip(): continue
        row = next(csv.reader([ln], delimiter='\t'))
        if row: existing.add(row[0])
# Now ensure your new JP sentences are not in `existing`.
```

## Verification step (mandatory before reporting success)

```bash
for f in <your 4-5 output files>; do
    ls -la $f
    grep -vE '^(#|$)' $f | wc -l
done
python3 validate_anki_data.py 2>&1 | tail -5
```

Report the exact ls + row counts + validator output. DO NOT claim
success if any file is missing or has wrong row count. The audit
machinery I run after you will detect lies and immediately re-spawn
the slice.

## Reference examples

Wave 1 and Wave 2 TSVs under `grammar/00-foundation/` and
`grammar/01-n5/` are the canonical reference for exact formatting.
Open any of them to compare.
