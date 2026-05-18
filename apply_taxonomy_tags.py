#!/usr/bin/env python3
"""
Auto-injects taxonomy tags into every TSV under ./grammar/.

Tag axes (see CONTENT_PLAN.md § Tagging taxonomy):
  module:NN-name  jlpt:n5..n1|beyond  register:*  frequency:*  domain:*
  point:slug      pos:*

This script is idempotent — it only ADDS missing tags. Existing tags
are preserved (and de-duplicated). Tags axis values are inferred from
the file's path + filename (module, jlpt level, point slug) and from
the row content (register / pos / domain heuristics).

Usage:
    python scripts/apply_taxonomy_tags.py [--dry-run] [grammar/<subdir>]
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

GRAMMAR_DIR = Path("grammar-strict")

MODULE_TO_JLPT = {
    "01-n5": "n5", "02-n4": "n4", "03-n3": "n3",
    "04-n2": "n2", "05-n1": "n1",
    "00-foundation": "n5",
    "12-beyond-n1": "beyond",
}

MODULE_TO_SOURCE = {
    "00-foundation": "source:curated-jpgram",
    "01-n5": "source:shin-kanzen",
    "02-n4": "source:shin-kanzen",
    "03-n3": "source:shin-kanzen",
    "04-n2": "source:shin-kanzen",
    "05-n1": "source:shin-kanzen",
    "06-keigo": "source:dictionary-of-jp-grammar",
    "07-casual": "source:imabi",
    "08-slang": "source:tofugu",
    "09-sfp-aizuchi": "source:dictionary-of-jp-grammar",
    "10-onomatopoeia": "source:dictionary-of-jp-grammar",
    "11-classical": "source:imabi",
    "12-beyond-n1": "source:dictionary-of-jp-grammar",
    "13-l1": "source:curated-jpgram",
}


def derive_path_tags(path: Path) -> list[str]:
    """Tags inferred purely from file location + name."""
    tags: list[str] = []
    parts = path.parts
    # module
    for p in parts:
        if re.match(r"^\d\d-", p):
            tags.append(f"module:{p}")
            if p in MODULE_TO_JLPT:
                tags.append(f"jlpt:{MODULE_TO_JLPT[p]}")
            tags.append(MODULE_TO_SOURCE.get(p, "source:curated-jpgram"))
            break
    # point slug = filename stem minus the trailing _<notetype>
    stem = path.stem
    for nt in ("recognition", "production", "cloze", "contrast", "listening", "dictation"):
        if stem.endswith(f"_{nt}"):
            stem = stem[: -len(nt) - 1]
            break
    if stem and not stem.startswith("module-"):
        tags.append(f"point:{stem}")
    return tags


# ---------------------------------------------------------------- frequency
# JLPT vocab → frequency-band lookup. Built lazily so the script still runs
# if data/frequency-lists/ is not present.
_FREQ_INDEX: dict[str, str] | None = None

def _load_freq_index() -> dict[str, str]:
    """Return word→band map. Bands: top1k, top5k, top10k, low."""
    global _FREQ_INDEX
    if _FREQ_INDEX is not None:
        return _FREQ_INDEX
    import csv as _csv
    idx: dict[str, str] = {}
    jlpt_dir = Path("data/frequency-lists/jlpt")
    if jlpt_dir.exists():
        # N5 = top1k, N4 = top5k, N3 = top10k, N2/N1 = low
        for level, band in [("n5", "top1k"), ("n4", "top5k"),
                             ("n3", "top10k"), ("n2", "low"),
                             ("n1", "low")]:
            p = jlpt_dir / f"{level}.csv"
            if not p.exists(): continue
            with p.open(encoding="utf-8", newline="") as fh:
                r = _csv.DictReader(fh)
                for row in r:
                    w = (row.get("expression") or "").strip()
                    if w and w not in idx:
                        idx[w] = band
    _FREQ_INDEX = idx
    return idx


def derive_frequency_tag(jp: str) -> list[str]:
    """Tag the lexically-rarest CJK word in the sentence (high signal)."""
    idx = _load_freq_index()
    if not idx: return []
    # Crude: walk every 1-4 char substring, prefer longest match per starting position
    found_bands: set[str] = set()
    BAND_RANK = {"top1k": 0, "top5k": 1, "top10k": 2, "low": 3}
    i = 0
    while i < len(jp):
        if "\u4e00" <= jp[i] <= "\u9fff" or "\u30a0" <= jp[i] <= "\u30ff":
            for L in range(min(4, len(jp) - i), 0, -1):
                sub = jp[i:i+L]
                if sub in idx:
                    found_bands.add(idx[sub])
                    i += L; break
            else: i += 1
        else: i += 1
    if not found_bands: return []
    # Tag the RAREST band found (signals the difficulty floor of the sentence)
    rarest = max(found_bands, key=lambda b: BAND_RANK[b])
    return [f"frequency:{rarest}"]


# ---------------------------------------------------------------- complexity
def derive_complexity_tag(jp: str) -> list[str]:
    """Stratify within a JLPT level: intro / standard / advanced.

    Heuristic: mora-equivalent length + presence of subclause markers.
    """
    # Strip cloze markers + punctuation for length count
    body = re.sub(r"\{\{c\d+::[^}]+\}\}", "X", jp)
    body = re.sub(r"[。、！？\s]", "", body)
    length = len(body)
    # Subclauses: と思う, ので, から (causal), が (concessive), て-form chains
    subclauses = (body.count("から") + body.count("ので") + body.count("けど") +
                  body.count("が、") + body.count("し、") + body.count("たり") +
                  body.count("という") + body.count("という"))
    if length < 12 and subclauses <= 1:
        return ["complexity:intro"]
    if length < 25 and subclauses <= 2:
        return ["complexity:standard"]
    return ["complexity:advanced"]


# ---------------------------------------------------------------- confusable-with
def derive_confusable_tags(row: list[str], header: list[str]) -> list[str]:
    """For Contrast rows, link to the alternate (OptionB if Answer=OptionA, else OptionA)."""
    if "OptionA" not in header or "OptionB" not in header or "Answer" not in header:
        return []
    try:
        a = row[header.index("OptionA")].strip()
        b = row[header.index("OptionB")].strip()
        ans = row[header.index("Answer")].strip()
    except IndexError:
        return []
    if not (a and b and ans): return []
    # Slugify the *other* option for the tag value
    other = b if ans == a else a if ans == b else None
    if not other: return []
    slug = re.sub(r"[^A-Za-z0-9\u3040-\u30ff\u4e00-\u9fff]+", "-", other).strip("-")
    if not slug: return []
    return [f"confusable-with:{slug}"]


def merge_tags(existing: str, new: list[str]) -> str:
    """Merge tag strings, de-duplicate, preserve order (existing first)."""
    seen: dict[str, None] = {}
    for t in (existing or "").split():
        if t:
            seen[t] = None
    for t in new:
        if t:
            seen[t] = None
    return " ".join(seen.keys())


def process_file(path: Path, dry_run: bool) -> int:
    """Returns number of rows whose tag column changed."""
    src = path.read_text(encoding="utf-8")
    lines = src.splitlines(keepends=True)
    header = None
    for line in lines:
        if line.startswith("#columns:"):
            header = line.lstrip("#").rstrip("\n").split("\t")
            header[0] = header[0].replace("columns:", "")
            break
    if not header:
        print(f"  skip (no #columns): {path}", file=sys.stderr)
        return 0
    if header[-1].lower() != "tags":
        print(f"  skip (last column not Tags): {path}", file=sys.stderr)
        return 0

    path_tags = derive_path_tags(path)

    out: list[str] = []
    changed = 0
    for line in lines:
        if not line.strip() or line.startswith("#"):
            out.append(line)
            continue
        # parse single TSV row
        row = next(csv.reader([line.rstrip("\n")], delimiter="\t", quotechar='"'))
        if len(row) != len(header):
            out.append(line)
            continue
        # Compose all axes: path-derived + content-derived (per-row)
        jp = row[0]  # column 0 is JP for all note types except Production
        if "Sample" in header and path.stem.endswith("_production"):
            sample = row[header.index("Sample")]
            if re.search(r"[一-龯ぁ-んァ-ン]", sample):
                jp = sample
            elif "Target" in header:
                jp = row[header.index("Target")]
            else:
                jp = sample
        row_tags = list(path_tags)
        row_tags += derive_frequency_tag(jp)
        row_tags += derive_complexity_tag(jp)
        row_tags += derive_confusable_tags(row, header)
        merged = merge_tags(row[-1], row_tags)
        if merged != (row[-1] or "").strip():
            row[-1] = merged
            changed += 1
        # serialise back as TSV
        sio = []
        for cell in row:
            if "\t" in cell or '"' in cell:
                sio.append('"' + cell.replace('"', '""') + '"')
            else:
                sio.append(cell)
        out.append("\t".join(sio) + "\n")
    if changed and not dry_run:
        path.write_text("".join(out), encoding="utf-8")
    return changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default=str(GRAMMAR_DIR))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    root = Path(args.root)
    files = sorted(root.rglob("*.tsv"))
    total = 0
    for f in files:
        n = process_file(f, args.dry_run)
        if n:
            print(f"  {'[dry-run] ' if args.dry_run else ''}{f}: +tags on {n} rows")
        total += n
    print(f"\n{'Would update' if args.dry_run else 'Updated'} {total} rows across {len(files)} file(s).")


if __name__ == "__main__":
    main()
