#!/usr/bin/env bash
# Bootstrap script: download every external data resource the build
# pipeline depends on. Idempotent — skips anything already on disk.
#
# Usage:
#   bash setup_data.sh
#
# Total footprint after a clean run: ~54 MB.
# Per-resource license + provenance: see data/<subdir>/MANIFEST.md.
#
# Resources downloaded:
#   dictionaries/     JMdict_e, JMnedict, KANJIDIC2, RADKFILE, KRADFILE,
#                     Tatoeba JP sentences          (~27 MB)
#   pitch-accent/     Kanjium accents.txt + accents.sqlite,
#                     NHK pronunciation CSV          (~25 MB)
#   frequency-lists/  JLPT N5–N1 vocab, Wikipedia/Aozora/News/Twitter
#                     kanji frequency lists           (~2 MB)
#   grammar-refs/     Tofugu TOC + Yomitan catalog HTML caches (~0.5 MB)
#
# Failures are tolerated and noted on stdout — partial datasets still
# let the pipeline build (each script degrades gracefully).

set -u
mkdir -p data/{dictionaries,pitch-accent,pitch-accent/nhk,frequency-lists,frequency-lists/jlpt,grammar-refs,readme-cache,corpora}

log() { printf '\n→ %s\n' "$*"; }
get() {
    # get URL OUTFILE  → skip if already present and non-empty
    local url="$1" out="$2"
    if [[ -s "$out" ]]; then
        printf '  ✓ exists: %s\n' "$out"
        return 0
    fi
    printf '  fetching → %s\n' "$out"
    curl -fsSL --retry 3 --connect-timeout 15 -o "$out" "$url" \
        && printf '  ✓ ok (%s bytes)\n' "$(wc -c < "$out" | tr -d ' ')" \
        || { printf '  ✗ FAILED: %s\n' "$url"; rm -f "$out"; return 1; }
}

# ── 1. Dictionaries (EDRDG + Tatoeba) ──────────────────────────────
log "1. Dictionaries (EDRDG + Tatoeba)"
get http://ftp.edrdg.org/pub/Nihongo/JMdict_e.gz       data/dictionaries/JMdict_e.gz       || :
get http://ftp.edrdg.org/pub/Nihongo/JMnedict.xml.gz   data/dictionaries/JMnedict.xml.gz   || :
get http://ftp.edrdg.org/pub/Nihongo/kanjidic2.xml.gz  data/dictionaries/kanjidic2.xml.gz  || :
get http://ftp.edrdg.org/pub/Nihongo/radkfile.gz       data/dictionaries/radkfile.gz       || :
get http://ftp.edrdg.org/pub/Nihongo/kradfile.gz       data/dictionaries/kradfile.gz       || :
get https://downloads.tatoeba.org/exports/per_language/jpn/jpn_sentences.tsv.bz2 \
    data/dictionaries/jpn_sentences.tsv.bz2 || :

# ── 2. Pitch-accent (Kanjium + NHK) ────────────────────────────────
log "2. Pitch-accent (Kanjium + NHK)"
get https://raw.githubusercontent.com/mifunetoshiro/kanjium/master/data/source_files/raw/accents.txt \
    data/pitch-accent/kanjium_accents.txt || :
# NHK pronunciation dump (cloned via tar archive of the repo's master branch).
if [[ ! -s data/pitch-accent/nhk_accents.csv ]]; then
    log "   building NHK accents CSV from javdejong/nhk-pronunciation"
    tmp=$(mktemp -d)
    curl -fsSL https://github.com/javdejong/nhk-pronunciation/archive/refs/heads/master.tar.gz \
        | tar -xzf - -C "$tmp" 2>/dev/null \
        && cp "$tmp"/nhk-pronunciation-master/ACCDB_unicode.csv data/pitch-accent/nhk_accents.csv 2>/dev/null \
        && printf '  ✓ NHK CSV staged\n' \
        || printf '  ✗ NHK fetch failed\n'
    rm -rf "$tmp"
fi
# Build accents.sqlite from kanjium_accents.txt + symlink the canonical path.
if [[ -s data/pitch-accent/kanjium_accents.txt && ! -s data/pitch-accent/accents.sqlite ]]; then
    log "   indexing kanjium accents into SQLite"
    python3 - <<'PY'
import sqlite3, csv, os
src = "data/pitch-accent/kanjium_accents.txt"
db  = "data/pitch-accent/accents.sqlite"
con = sqlite3.connect(db)
con.execute("CREATE TABLE IF NOT EXISTS accents(id INTEGER PRIMARY KEY, expression TEXT, reading TEXT, accent TEXT)")
con.execute("DELETE FROM accents")
n = 0
with open(src, encoding="utf-8") as f:
    for row in csv.reader(f, delimiter="\t"):
        if len(row) < 3: continue
        con.execute("INSERT INTO accents(expression, reading, accent) VALUES(?,?,?)", row[:3])
        n += 1
con.execute("CREATE INDEX IF NOT EXISTS ix_expression ON accents(expression)")
con.commit(); con.close()
print(f"  ✓ indexed {n} entries → {db}")
PY
fi
[[ -L data/accents.sqlite || -e data/accents.sqlite ]] || ln -s pitch-accent/accents.sqlite data/accents.sqlite

# ── 3. Frequency lists (JLPT vocab + kanji freq) ───────────────────
log "3. Frequency lists (JLPT vocab + kanji freq)"
for n in 1 2 3 4 5; do
    get "https://raw.githubusercontent.com/jamsinclair/open-anki-jlpt-decks/main/src/n${n}.csv" \
        "data/frequency-lists/jlpt/n${n}.csv" || :
done
for corpus in wikipedia aozora news twitter; do
    get "https://raw.githubusercontent.com/scriptin/topokanji/master/lists/kanji-frequency-${corpus}.json" \
        "data/frequency-lists/kanji_${corpus}_frequency.json" || :
done

# ── 4. Grammar references (Tofugu + Yomitan catalog HTML caches) ───
log "4. Grammar references"
get "https://www.tofugu.com/japanese-grammar/" \
    data/grammar-refs/tofugu_grammar_toc.html || :
get "https://raw.githubusercontent.com/MarvNC/YomichanDictionaries/main/README.md" \
    data/readme-cache/yomitan_dictionaries.md || :

log "DONE."
echo "Run: python3 build_pitchaccent.py --report-missing | head"
echo "to verify the pitch-accent index builds."
