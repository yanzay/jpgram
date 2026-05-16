# `grammar/` — corpus root

One sub-directory per module. File naming convention:

```
grammar/<module>/<point-slug>_<notetype>.tsv
```

Where `<notetype>` is one of `recognition`, `production`, `cloze`, `contrast`
(matched by `build_anki_package.detect_note_type()`).

Each TSV begins with an Anki-format `#columns:` directive whose tabs split
into exactly the field list declared in `build_anki_package.NOTE_TYPES`
for that note type.

## Modules

| Dir | Module | Wave |
|---|---|---|
| `00-foundation/` | Kana, particles, copula, counters | 1 |
| `01-n5/` | N5 grammar (~140 points) | 2 |
| `02-n4/` | N4 grammar (~150 points) | 3 |
| `03-n3/` | N3 grammar (~190 points) | 4 |
| `04-n2/` | N2 grammar (~220 points) | 5 |
| `05-n1/` | N1 grammar (~260 points) | 6 |
| `06-keigo/` | Sonkeigo / kenjōgo / teineigo / bikago | 7 |
| `07-casual/` | -てる / -ちゃう / -じゃん etc. | 8 |
| `08-slang/` | Modern + internet slang | 9 |
| `09-sfp-aizuchi/` | Sentence-final particles + aizuchi | 10 |
| `10-onomatopoeia/` | 擬音語・擬態語 | 11 |
| `11-classical/` | Carryover from 古文 / 文語 | 12 |
| `12-beyond-n1/` | 四字熟語・ことわざ・慣用句 | 13 |
| `13-l1/` | Per-L1 contrast drills | 14 |

See [`../CONTENT_PLAN.md`](../CONTENT_PLAN.md) for the full content plan.
