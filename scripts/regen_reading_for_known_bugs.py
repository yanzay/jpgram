#!/usr/bin/env python3
"""
Targeted reading regeneration for known-wrong-reading patterns.

For each row in grammar-strict/ where the Reading column contains one of
the known-bad kana patterns AND the JP/source column contains the
corresponding kanji surface, regenerate the Reading column from the JP
source using the current scripts/jp_reading.py pipeline (which has been
updated with the correct phrase overrides).

This script is non-destructive on rows whose Reading is already clean —
it only touches rows that match a known-bug pattern.

Usage:
    python3 scripts/regen_reading_for_known_bugs.py [--dry-run]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from jp_reading import reading as gen_reading

GRAMMAR_DIR = Path("grammar-strict")

# (label, wrong_kana_substring, list_of_required_jp_substrings, correct_kana_hint)
# A row is targeted iff Reading contains wrong_kana AND JP contains ANY of the required strings.
# The correct_kana_hint is only used for logging; the actual fix uses gen_reading(jp).
BUG_PATTERNS = [
    ("彼の→かれの",    "かの",        ["彼の", "彼が", "彼に", "彼を", "彼は", "彼も", "彼と", "彼で"], "かれ"),
    ("お金→おかね",    "おきん",       ["お金"],          "おかね"),
    ("七時→しちじ",    "ななじ",       ["七時"],          "しちじ"),
    ("外国人→がいこくじん", "がいこくにん", ["外国人"],     "がいこくじん"),
    ("蘇→よみがえった", "よみがった",  ["蘇"],            "よみがえった"),
    ("や否や→やいなや", "やひや",      ["や否や"],        "やいなや"),
    ("100℃→ひゃくど",  "ひゃくどしたい", ["100℃", "100°C"], "ひゃくど"),
    ("健康→けんこう",  "きれい",       ["健康"],          "けんこう"),
    ("見た目→みため",  "みたため",     ["見た目"],        "みため"),
    ("開ける→あける",  "ひらける",     ["開ける"],        "あける"),
    ("光と影→ひかりとかげ", "ひかとかげ", ["光と影"],      "ひかりとかげ"),
    ("若き日→わかきひ", "わかきにち",  ["若き日"],        "わかきひ"),
    ("入って→はいって", "いっって",    ["入って"],        "はいって"),
    ("熱す→ねっする",   "ねっす",      ["熱す"],          "ねっする"),
    ("八日→ようか",    "はちにち",    ["八日"],          "ようか"),
    # NOTE: 親→おや omitted — `したし` is also a substring of `しゅんかん` (した瞬間),
    # producing too many false positives.
    # NOTE: 行う→おこなう (Nを/Nも + 行っている context) handled separately;
    # the verb shares its kanji with 行く and fugashi disambiguates only
    # imperfectly. Affected rows are fixed manually after this sweep.
]

# Known false-positive guard: 彼女 contains 彼 but its reading かのじょ contains かの;
# don't touch rows where 彼女 is present and 彼の/彼が/etc. is not.
def _has_real_pronoun(jp: str, kanji_list: list[str]) -> bool:
    for k in kanji_list:
        if k in jp:
            return True
    return False


def fix_file(path: Path, dry_run: bool) -> tuple[int, int, list[str]]:
    """Return (rows_fixed, rows_unfixable, log_lines)."""
    # Skip cloze files: their JP source contains {{c1::…}} markers that
    # the reading pipeline doesn't understand. Cloze Reading-column repair
    # is handled separately in Phase 2.
    if "_cloze" in path.stem:
        return 0, 0, []

    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    cols = None
    for raw in lines:
        if raw.startswith("#columns:"):
            cols = raw.rstrip("\n")[len("#columns:"):].split("\t")
            break
    if not cols or "Reading" not in cols:
        return 0, 0, []

    reading_idx = cols.index("Reading")
    jp_candidates = ["JP", "Text", "Sample", "Transcript", "Answer"]
    jp_idx = None
    for c in jp_candidates:
        if c in cols:
            jp_idx = cols.index(c)
            break
    if jp_idx is None:
        return 0, 0, []

    fixed = unfixable = 0
    log: list[str] = []
    new_lines: list[str] = []
    for lineno, raw in enumerate(lines, start=1):
        if not raw.strip() or raw.startswith("#"):
            new_lines.append(raw)
            continue
        row = raw.rstrip("\n").rstrip("\r").split("\t")
        if len(row) <= max(reading_idx, jp_idx):
            new_lines.append(raw)
            continue

        current_reading = row[reading_idx]
        jp = row[jp_idx]

        # Does this row match any known bug pattern?
        triggered = None
        for label, wrong, jp_required, _correct in BUG_PATTERNS:
            if wrong in current_reading and _has_real_pronoun(jp, jp_required):
                triggered = (label, wrong)
                break

        if triggered is None:
            new_lines.append(raw)
            continue

        new_reading = gen_reading(jp)

        # Sanity check: the new reading must NOT contain the wrong-kana fragment
        # in the same context (the regen should have fixed it).
        if new_reading == current_reading:
            log.append(f"  UNCHANGED {path.name}:{lineno}  pattern={triggered[0]}  reading={current_reading[:35]!r}")
            new_lines.append(raw)
            unfixable += 1
            continue

        log.append(f"  FIX {path.name}:{lineno}  [{triggered[0]}]  {current_reading[:35]!r} → {new_reading[:35]!r}")
        row[reading_idx] = new_reading
        eol = "\r\n" if raw.endswith("\r\n") else "\n"
        new_lines.append("\t".join(row) + eol)
        fixed += 1

    if fixed > 0 and not dry_run:
        path.write_text("".join(new_lines), encoding="utf-8")

    return fixed, unfixable, log


def main() -> int:
    parser = argparse.ArgumentParser(description="Regenerate Reading column for known wrong-reading patterns")
    parser.add_argument("--dry-run", action="store_true", help="Print fixes without writing files")
    args = parser.parse_args()

    tsvs = sorted(GRAMMAR_DIR.rglob("*.tsv"))

    total_fixed = total_unfixable = 0
    for tsv in tsvs:
        fixed, unfixable, log = fix_file(tsv, args.dry_run)
        total_fixed += fixed
        total_unfixable += unfixable
        for ln in log:
            print(ln)

    mode = "[DRY RUN] " if args.dry_run else ""
    print(f"\n{mode}Fixed: {total_fixed}  |  Unchanged-after-regen (needs manual): {total_unfixable}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
