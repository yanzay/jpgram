#!/usr/bin/env python3
"""
Phase-9 follow-up: trim recognition files where rows have drifted
off-topic from the filename's grammar slug.

For each recognition file (excluding aggregator/category slugs), classify
each row as on-topic or off-topic by checking whether the filename slug
(or a verb-stem alias) appears in either the JP or Reading column.

Actions:
- ≥5 on-topic rows: keep all on-topic rows; drop off-topic. Trim to 8
  rows max to avoid bloated files.
- 1–4 on-topic rows: same — drop off-topic but the file is now small;
  flag for follow-up authoring (printed to the report).
- 0 on-topic rows: leave file untouched; print as NEEDS-REAUTHOR. These
  cannot be safely auto-trimmed.

Usage:  python3 scripts/_phase9_trim_offtopic_recognition.py [--dry-run]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

GRAMMAR_DIR = Path("grammar-strict")

CATEGORY_SLUGS = frozenset({
    "kana", "copula", "particles-core", "numbers-counters",
    "demonstratives", "time-expressions", "pitch-accent-primer",
    "i-adjectives", "interrogatives", "polite-verb-endings",
    "verb-non-past", "past-tense-い-adjectives", "causative-passive",
    "causative", "potential", "passive",
    # Single-char umbrella slugs (treated as categories)
    "いい", "それ", "どこ", "って", "と", "が", "を", "に", "で", "の",
    "は", "も", "へ", "や", "か", "から", "まで",
    # Onomatopoeia bucket files
    "onomatopoeia", "giongo-sounds", "gitaigo-states", "giseigo-people",
    "giseigo-voices", "emotional-onomatopoeia",
    # L1 bucket files
    "l1-tense-aspect", "l1-articles-and-number", "l1-pronoun-overuse",
    "l1-yes-no_negative-questions", "l1-givereceive-direction",
    "l1-particles-overlap", "l1-relative-clauses",
})


def slug_aliases(slug: str) -> set[str]:
    """Generate substring aliases that should match any conjugated form
    of the grammar point in the JP/Reading text. Only adds aliases with
    ≥2 chars to avoid over-permissive 1-char matches."""
    aliases = {slug}
    MIN = 2
    # Strip trailing copula だ/です — match the bare noun form (予定だ → 予定)
    for cop in ("だ", "です"):
        if slug.endswith(cop):
            bare = slug[:-len(cop)]
            if len(bare) >= MIN:
                aliases.add(bare)
    # Strip trailing する → add the renyokei stem (にする → にし; 化する → 化し)
    if slug.endswith("する"):
        bare = slug[:-2]
        ren = bare + "し"
        if len(ren) >= MIN:
            aliases.add(ren)
    # Strip trailing くる (irregular カ変) → add 〜き
    if slug.endswith("くる"):
        bare = slug[:-2]
        ren = bare + "き"
        if len(ren) >= MIN:
            aliases.add(ren)
    # Other godan/ichidan: dict-form ending + renyokei
    if slug and slug[-1] in "うるくぐすつぬむぶ":
        stem = slug[:-1]
        if len(stem) >= MIN:
            aliases.add(stem)
        # godan → -i renyokei
        renyokei = {"う": "い", "く": "き", "ぐ": "ぎ", "す": "し",
                    "つ": "ち", "ぬ": "に", "む": "み", "ぶ": "び"}
        if slug[-1] in renyokei:
            ren = stem + renyokei[slug[-1]]
            if len(ren) >= MIN:
                aliases.add(ren)
    # i-adjective: strip the trailing い + add -く (adverbial) and -かった (past)
    if slug.endswith("い") and len(slug) >= 3:
        stem = slug[:-1]
        if len(stem) >= MIN:
            aliases.add(stem)
    return aliases


def has_kana(s: str) -> bool:
    return any("぀" <= c <= "ゟ" for c in s)


def trim_file(path: Path, dry_run: bool) -> tuple[str, int, int, int]:
    """Return (status, original_rows, on_topic_rows, kept_rows)."""
    slug = path.stem[:-len("_recognition")]
    if slug in CATEGORY_SLUGS:
        return ("skip-category", 0, 0, 0)
    if "-" in slug or any(c.isdigit() for c in slug) or "[" in slug \
       or "・" in slug or "～" in slug or "(" in slug:
        return ("skip-aggregator", 0, 0, 0)
    if not has_kana(slug):
        return ("skip-non-hiragana", 0, 0, 0)

    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    cols = None
    for raw in lines:
        if raw.startswith("#columns:"):
            cols = raw[len("#columns:"):].rstrip("\n").split("\t")
            break
    if not cols or "JP" not in cols or "Reading" not in cols:
        return ("skip-no-cols", 0, 0, 0)
    jp_idx = cols.index("JP")
    reading_idx = cols.index("Reading")

    aliases = slug_aliases(slug)
    header_lines: list[str] = []
    on_topic_rows: list[str] = []
    off_topic_rows: list[str] = []
    for raw in lines:
        if raw.startswith("#") or not raw.strip():
            header_lines.append(raw)
            continue
        parts = raw.split("\t")
        if len(parts) <= max(jp_idx, reading_idx):
            header_lines.append(raw)
            continue
        jp = parts[jp_idx]
        reading = parts[reading_idx]
        if any(a in jp or a in reading for a in aliases):
            on_topic_rows.append(raw)
        else:
            off_topic_rows.append(raw)

    total = len(on_topic_rows) + len(off_topic_rows)
    if total < 5:
        return ("skip-tiny", total, len(on_topic_rows), total)

    on_topic_count = len(on_topic_rows)
    pct = on_topic_count / total if total else 0

    # Don't touch files already premium-quality
    if pct >= 0.80 and total <= 8:
        return ("clean", total, on_topic_count, total)

    if on_topic_count == 0:
        # Can't auto-trim; needs hand-authoring
        return ("needs-reauthor", total, 0, total)

    # Phase-9+ policy: ALWAYS trim if any on-topic rows exist, even if
    # we end up with <5 rows. A small all-correct file is better than a
    # bloated mostly-wrong one. Files with <3 on-topic stay flagged
    # `needs-supplementing` for the caller; files with 0 on-topic stay
    # untouched as `needs-reauthor` (caller will reauthor in batch).
    if on_topic_count < 3:
        if on_topic_count == 0:
            return ("needs-reauthor", total, 0, total)
        return ("needs-supplementing", total, on_topic_count, total)

    # ≥3 on-topic: trim to on-topic only, cap at 8 for atomic card sets.
    kept = on_topic_rows[:8]
    if not dry_run and len(kept) != total:
        new_text = "".join(header_lines + kept)
        path.write_text(new_text, encoding="utf-8")

    if on_topic_count < 5:
        return ("trimmed-small", total, on_topic_count, len(kept))
    return ("trimmed", total, on_topic_count, len(kept))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    stats = {"clean": 0, "trimmed": 0, "needs-supplementing": 0,
             "needs-reauthor": 0, "skip-category": 0,
             "skip-aggregator": 0, "skip-non-hiragana": 0,
             "skip-no-cols": 0, "skip-tiny": 0}
    needs_reauthor: list[tuple[Path, int]] = []
    needs_supplementing: list[tuple[Path, int, int]] = []
    trimmed_total = 0

    for rec in sorted(GRAMMAR_DIR.rglob("*_recognition.tsv")):
        status, total, on_topic, kept = trim_file(rec, args.dry_run)
        stats[status] = stats.get(status, 0) + 1
        if status == "trimmed":
            trimmed_total += total - kept
        elif status == "needs-reauthor":
            needs_reauthor.append((rec, total))
        elif status == "needs-supplementing":
            needs_supplementing.append((rec, total, on_topic))

    mode = "[DRY RUN] " if args.dry_run else ""
    print(f"\n=== {mode}Phase-9 trim summary ===")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    print(f"\nSafe auto-trims: {trimmed_total} off-topic rows dropped from "
          f"{stats['trimmed']} files (each retains ≥5 on-topic rows).")
    print(f"\nNot auto-fixed (need hand-authoring follow-up):")
    print(f"  needs-reauthor (0 on-topic rows):       {len(needs_reauthor)}")
    print(f"  needs-supplementing (1-4 on-topic):     {len(needs_supplementing)}")
    print()
    for rec, total in needs_reauthor:
        print(f"  REAUTHOR    {rec}")
    for rec, total, on_topic in needs_supplementing[:30]:
        print(f"  SUPPLEMENT  {rec}  ({on_topic} on-topic of {total})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
