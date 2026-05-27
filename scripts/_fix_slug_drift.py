#!/usr/bin/env python3
"""
Trim large production/dictation/listening files that have real slug-drift:
keep only rows where the slug (or its aliases) appears in the source sentence.

For files where <5 on-topic rows result, validator skips the check.
For files where ≥5 rows remain, all kept rows are on-topic → passes.
"""
import csv, pathlib, re, sys

GRAMMAR = pathlib.Path("grammar-strict")

# Same alias logic as validate_anki_data.py IRREGULAR dict (kept in sync).
IRREGULAR = {
    "くる": {"くる", "きた", "きて", "きます", "き", "こない", "こよう"},
    "する": {"する", "した", "して", "します", "し", "しない", "しよう"},
    "ある": {"ある", "あり", "あって", "あった", "あります"},
    "がる": {"がる", "がっ", "がった", "がり", "たがる", "たがっ", "たがった"},
    "びる": {"びる", "びた", "びて", "びり"},
    "に反して": {"に反して", "に反した", "に反し"},
    "に応えて": {"に応えて", "に応えた", "に応え"},
    "に際して": {"に際して", "に際した", "に際し"},
    "にわたって": {"にわたって", "にわたった", "にわたる", "にわたり"},
    "を踏まえて": {"を踏まえて", "を踏まえた", "を踏まえ"},
    "たって": {"たって", "だって"},
    "ては": {"ては", "んでは"},
    "てならない": {"てならない", "でならない"},
    "ていては": {"ていては", "でいては"},
    "て初めて": {"て初めて", "で初めて"},
    "なりに": {"なりに", "なりの"},
    "折には": {"折には", "折に"},
    "に即して": {"に即して", "に即した", "に即し"},
    "を前提に": {"を前提に", "を前提と"},
    "ときいた": {"ときいた", "ときき", "ときいて", "ときいてい"},
    "がいる": {"がいる", "がいます", "がいません", "がい", "います", "いません"},
    "から言うと": {"から言うと", "から言えば", "から言って", "から言"},
    "化する": {"化する", "化し", "化さ", "化"},
    "てもかまわない": {"てもかまわない", "てもかまわ", "でもかまわ",
                       "かまいません", "かまいます", "かまわない"},
    "ごろ": {"ごろ", "ころ"},
    "とおり": {"とおり", "どおり"},
    "関係がある": {"関係がある", "関係がない", "関係が"},
}

_KANJI_READINGS = {
    "取": "と", "言": "い", "聞": "き", "見": "み",
    "従": "したが",
}


def get_aliases(slug: str) -> set[str]:
    if slug in IRREGULAR:
        return set(IRREGULAR[slug])
    aliases = {slug}
    MIN = 2

    def _is_kanji(ch):
        return "一" <= ch <= "鿿"

    for cop in ("だ", "です"):
        if slug.endswith(cop):
            bare = slug[:-len(cop)]
            if len(bare) >= MIN:
                aliases.add(bare)
    if slug.endswith("ない") and len(slug) >= 4:
        bare = slug[:-2]
        if len(bare) >= MIN:
            aliases.add(bare)
    if slug.endswith("する") and len(slug) > 2:
        ren = slug[:-2] + "し"
        if len(ren) >= MIN:
            aliases.add(ren)
    if slug.endswith("くる") and len(slug) > 2:
        ren = slug[:-2] + "き"
        if len(ren) >= MIN:
            aliases.add(ren)
    if slug and slug[-1] in "うるくぐすつぬむぶ":
        stem = slug[:-1]
        if len(stem) >= MIN or (len(stem) == 1 and _is_kanji(stem)):
            aliases.add(stem)
        renyokei = {"う": "い", "く": "き", "ぐ": "ぎ", "す": "し",
                    "つ": "ち", "ぬ": "に", "む": "み", "ぶ": "び"}
        if slug[-1] in renyokei:
            ren = stem + renyokei[slug[-1]]
            if len(ren) >= MIN:
                aliases.add(ren)
    if slug.endswith("い") and len(slug) >= 3:
        stem = slug[:-1]
        if len(stem) >= MIN:
            aliases.add(stem)
    # Kanji→hiragana
    hira = slug
    for k, v in _KANJI_READINGS.items():
        hira = hira.replace(k, v)
    if hira != slug and len(hira) >= MIN:
        aliases.add(hira)
    return aliases


def row_is_on_topic(nt: str, header: list, row: list, aliases: set) -> bool:
    # Build source text depending on note type
    src = ""
    reading = ""
    opt_a = opt_b = ""
    if nt == "Production":
        sample_idx = header.index("Sample") if "Sample" in header else -1
        target_idx = header.index("Target") if "Target" in header else -1
        src = (row[sample_idx] if sample_idx >= 0 else "") or (row[target_idx] if target_idx >= 0 else "")
        reading_idx = header.index("Reading") if "Reading" in header else -1
        reading = row[reading_idx] if reading_idx >= 0 else ""
    elif nt == "Dictation" or nt == "Listening":
        ans_idx = header.index("Answer") if "Answer" in header else -1
        trans_idx = header.index("Transcript") if "Transcript" in header else -1
        src = (row[ans_idx] if ans_idx >= 0 else "") or (row[trans_idx] if trans_idx >= 0 else "")
        reading_idx = header.index("Reading") if "Reading" in header else -1
        reading = row[reading_idx] if reading_idx >= 0 else ""
    return any(a in src or a in reading for a in aliases)


def trim_file(path: pathlib.Path, dry_run: bool = False) -> int:
    """Trim off-topic rows from path. Returns number of rows removed."""
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    headers = []
    data_start = 0
    nt = None
    col_header = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("#notetype:"):
            nt = stripped[len("#notetype:"):].strip()
        if stripped.startswith("#columns:"):
            col_header = [c.strip() for c in stripped[len("#columns:"):].split("\t")]
        if not stripped.startswith("#") and stripped:
            data_start = i
            break
        headers.append(line)

    if not nt or not col_header:
        print(f"  SKIP {path}: could not detect note type or columns")
        return 0

    # Extract slug from filename
    slug = path.stem
    for suf in ("_production", "_dictation", "_listening", "_recognition", "_cloze", "_contrast"):
        if slug.endswith(suf):
            slug = slug[:-len(suf)]
            break
    aliases = get_aliases(slug)

    data_lines = lines[data_start:]
    kept = []
    dropped = 0
    for line in data_lines:
        stripped = line.strip()
        if not stripped:
            continue
        row = next(csv.reader([stripped], delimiter="\t", quotechar='"'), None)
        if not row or len(row) != len(col_header):
            continue
        if row_is_on_topic(nt, col_header, row, aliases):
            kept.append(line if line.endswith("\n") else line + "\n")
        else:
            dropped += 1

    if dropped == 0:
        print(f"  OK   {path}: no rows to drop")
        return 0

    print(f"  TRIM {path}: drop {dropped} rows, keep {len(kept)}")
    if not dry_run:
        new_content = "".join(headers) + "".join(kept)
        path.write_text(new_content, encoding="utf-8")
    return dropped


# Files with confirmed real drift (large production files + dictation/listening).
TARGET_FILES = [
    # Large production files
    "02-n4/かどうか_production.tsv",
    "03-n3/うちに_production.tsv",
    "03-n3/ということだ_production.tsv",
    "03-n3/どころか_production.tsv",
    "03-n3/ほど_production.tsv",
    "04-n2/および_production.tsv",
    "04-n2/かねる_production.tsv",
    "04-n2/だけあって_production.tsv",
    "04-n2/にしたがって_production.tsv",
    "05-n1/とは_production.tsv",
    "05-n1/のなんのって_production.tsv",
    # Dictation/Listening files with off-topic rows
    "02-n4/より_dictation.tsv",
    "02-n4/より_listening.tsv",
    "03-n3/せいで_dictation.tsv",
    "03-n3/せいで_listening.tsv",
    "03-n3/ほど_dictation.tsv",
    "03-n3/ほど_listening.tsv",
]

if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    total_dropped = 0
    for rel in TARGET_FILES:
        p = GRAMMAR / rel
        if not p.exists():
            print(f"  MISSING: {p}")
            continue
        total_dropped += trim_file(p, dry_run=dry)
    print(f"\nTotal rows dropped: {total_dropped}")
