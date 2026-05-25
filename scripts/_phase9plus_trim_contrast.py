#!/usr/bin/env python3
"""
Trim contrast files where rows have drifted off-topic. Mirrors
scripts/_phase9_trim_offtopic_recognition.py but for `_contrast.tsv`.

A contrast row is on-topic if the slug (or a conjugation alias) appears
in either the JP field, OptionA, OptionB, or Answer.

Files with ≥3 on-topic rows: trim to keep only on-topic.
Files with 0-2 on-topic: flagged as needs-reauthor.

Usage: python3 scripts/_phase9plus_trim_contrast.py [--dry-run]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _phase9_trim_offtopic_recognition import (
    slug_aliases, has_kana, CATEGORY_SLUGS, GRAMMAR_DIR
)


def trim_contrast(path: Path, dry_run: bool) -> tuple[str, int, int]:
    slug = path.stem[:-len("_contrast")]
    if slug in CATEGORY_SLUGS:
        return ("skip-category", 0, 0)
    if "-" in slug or any(c.isdigit() for c in slug) or "[" in slug \
       or "・" in slug or "～" in slug or "(" in slug:
        return ("skip-aggregator", 0, 0)
    if not has_kana(slug):
        return ("skip-non-hiragana", 0, 0)

    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    cols = None
    for raw in lines:
        if raw.startswith("#columns:"):
            cols = raw[len("#columns:"):].rstrip("\n").split("\t")
            break
    if not cols:
        return ("skip-no-cols", 0, 0)
    needed = ["JP", "OptionA", "OptionB", "Answer"]
    if not all(c in cols for c in needed):
        return ("skip-no-cols", 0, 0)
    idx = {c: cols.index(c) for c in needed}

    aliases = slug_aliases(slug)
    header_lines, on_topic_rows, off_topic_rows = [], [], []
    for raw in lines:
        if raw.startswith("#") or not raw.strip():
            header_lines.append(raw)
            continue
        parts = raw.split("\t")
        if len(parts) <= max(idx.values()):
            header_lines.append(raw)
            continue
        fields = " ".join(parts[idx[c]] for c in needed)
        if any(a in fields for a in aliases):
            on_topic_rows.append(raw)
        else:
            off_topic_rows.append(raw)

    total = len(on_topic_rows) + len(off_topic_rows)
    if total < 5:
        return ("skip-tiny", total, len(on_topic_rows))

    on_topic = len(on_topic_rows)
    pct = on_topic / total
    if pct >= 0.80 and total <= 10:
        return ("clean", total, on_topic)

    if on_topic == 0:
        return ("needs-reauthor", total, 0)
    if on_topic < 3:
        return ("needs-supplementing", total, on_topic)

    kept = on_topic_rows[:8]
    if not dry_run and len(kept) != total:
        path.write_text("".join(header_lines + kept), encoding="utf-8")
    return ("trimmed", total, on_topic)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    stats = {}
    needs_reauthor, needs_supp = [], []
    for tsv in sorted(GRAMMAR_DIR.rglob("*_contrast.tsv")):
        status, total, on_topic = trim_contrast(tsv, args.dry_run)
        stats[status] = stats.get(status, 0) + 1
        if status == "needs-reauthor":
            needs_reauthor.append(tsv)
        elif status == "needs-supplementing":
            needs_supp.append((tsv, total, on_topic))

    mode = "[DRY RUN] " if args.dry_run else ""
    print(f"=== {mode}Contrast trim summary ===")
    for k, v in sorted(stats.items()):
        print(f"  {k}: {v}")
    print(f"\nNeeds reauthor: {len(needs_reauthor)}")
    for t in needs_reauthor:
        print(f"  REAUTHOR {t}")
    print(f"\nNeeds supplementing: {len(needs_supp)}")
    for t, total, on_topic in needs_supp:
        print(f"  SUPPLEMENT {t}  ({on_topic}/{total})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
