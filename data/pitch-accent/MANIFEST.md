# Japanese Pitch-Accent Data Manifest

Date: 2026-05-16

| File | Source | License | Size | SHA256 | Purpose |
|------|--------|---------|------|--------|---------|
| `accents.sqlite` | Kanjium (compiled from accents.txt) | [MIT](https://github.com/mifunetoshiro/kanjium/blob/master/LICENSE) | 5.5 MB | Primary pitch-accent lookup database; indexed by expression for O(1) queries |
| `accents.txt` | [mifunetoshiro/kanjium](https://github.com/mifunetoshiro/kanjium/blob/master/data/source_files/raw/accents.txt) | [MIT](https://github.com/mifunetoshiro/kanjium/blob/master/LICENSE) | 3.1 MB | Raw source (TSV: word, reading, accent_number); 106,925 entries |
| `kanjium_accents.txt` | [mifunetoshiro/kanjium](https://github.com/mifunetoshiro/kanjium) (copy) | [MIT](https://github.com/mifunetoshiro/kanjium/blob/master/LICENSE) | 3.1 MB | Duplicate for reference; same as accents.txt |
| `nhk_accents.csv` | [javdejong/nhk-pronunciation](https://github.com/javdejong/nhk-pronunciation) | [MIT](https://github.com/javdejong/nhk-pronunciation/blob/master/LICENSE) | 14 MB | NHK Pronunciation Dictionary; fallback source (14M+ entries with pitch accent data) |

## SHA256 Verification

```
b3746a8ae0051df702f9459c98635df6d7d49eaf5108a10b26e31dba760c2626  accents.sqlite
8bd0dd127dab32ceec94cb03ab1ba6b68858ea73421dfa1731af2f373deb4f20  accents.txt
8bd0dd127dab32ceec94cb03ab1ba6b68858ea73421dfa1731af2f373deb4f20  kanjium_accents.txt
0b450bce4520c7121eddaa445607e4e7a650d96a9bbdf3fdea59f3db06330ed4  nhk_accents.csv
```

## Build Notes

- **accents.sqlite** was built from accents.txt using SQLite3 on 2026-05-16
- Schema: `CREATE TABLE accents (id INTEGER PRIMARY KEY, expression TEXT, reading TEXT, accent INTEGER); CREATE INDEX idx_expression ON accents(expression)`
- The script `data/accents.sqlite` is a symlink to `data/pitch-accent/accents.sqlite` for compatibility with `build_pitchaccent.py`
- JmdictFurigana was not available (no public release archive found); only Kanjium + NHK are staged

## License Summary

All files are under permissive licenses (MIT):
- **Kanjium** ([MIT License](https://github.com/mifunetoshiro/kanjium/blob/master/LICENSE)) — freely distributable
- **NHK Pronunciation** ([MIT License](https://github.com/javdejong/nhk-pronunciation/blob/master/LICENSE)) — freely distributable

