#!/usr/bin/env python3
"""A1 — MainUse-vs-JP keyword drift detector.

For each Recognition row, if MainUse references a specific verb-conjugation
surface (e.g. V-ません, V-ました) but that surface does NOT appear in JP, flag
it. The MainUse is teaching the wrong form for the example sentence.

Also produces A4 results (parity Recognition.MainUse == Production.Why with
same JP/Sample and A1-firing) inline.

Stdlib only.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parent.parent / "grammar-strict"

# Multi-character distinctive conjugation surfaces.
SURFACES = [
    "ませんでした",
    "ていません",
    "ていない",
    "ています",
    "ている",
    "ていた",
    "ましょう",
    "ました",
    "ません",
    "でした",
    "たがって",
    "たがる",
]

# Surface equivalents — if any equivalent of the flagged surface is present in
# JP, the MainUse is teaching a valid (just differently-conjugated) form of the
# same grammar point, so suppress the flag.
EQUIVALENTS = {
    # Include rendaku voiced variants (て→で) since these are the same te-form.
    "ている": ["ている", "ています", "ていた", "ていました", "ていない", "ていません",
             "でいる", "でいます", "でいた", "でいました", "でいない", "でいません"],
    "ています": ["ています", "ている", "ていた", "ていました",
              "でいます", "でいる", "でいた", "でいました"],
    "ていた": ["ていた", "ていました", "ている", "ています",
             "でいた", "でいました", "でいる", "でいます"],
    "ていない": ["ていない", "ていません", "でいない", "でいません"],
    "ていません": ["ていません", "ていない", "でいません", "でいない"],
    "ました": ["ました", "ません", "ませんでした"],  # general past polite
    "ません": ["ません", "ませんでした"],
    "ませんでした": ["ませんでした"],
    "ましょう": ["ましょう", "ませんか"],
    "でした": ["でした"],
    "たがる": ["たがる", "たがって", "たがっている", "たがっています", "たがった"],
    "たがって": ["たがって", "たがる", "たがっている", "たがっています"],
}

# False-positive sequences: if any of these tokens appear in JP, the surface is
# part of a compound and not a verb conjugation reference.
COMPOUND_CONTEXTS = {
    "たがって": ["にしたがって", "に従って", "従って", "したがって"],
    "たがる": ["にしたがる"],
}

# Only flag if surface appears in MainUse as a *form reference*. Patterns:
#  - "V-<surface>" or "Vて-<surface>" — hyphen prefix
#  - "<surface>:" — colon after
#  - "<surface>" as a free-standing token bounded by ASCII / spaces / punctuation
#  - "form: <surface>" / "(<surface>)" / "「<surface>」"
FORM_HINTS = [
    re.compile(r"[VA一-龠ぁ-んァ-ンー]\-(?P<s>{surface})"),  # V-ました
    re.compile(r"(?P<s>{surface})\s*[:：]"),  # ました:
    re.compile(r"[（(「『\"'\s](?P<s>{surface})[）)」』\"',.\s;:/=]"),  # 「ました」
    re.compile(r"^(?P<s>{surface})[\s:：（(「『]"),  # start of cell
    re.compile(r"=\s*(?P<s>{surface})"),  # = ました
]


def is_form_reference(mainuse: str, surface: str) -> bool:
    """Heuristic: surface appears as a form reference, not incidental."""
    padded = " " + mainuse + " "
    for pat in FORM_HINTS:
        rx = re.compile(pat.pattern.format(surface=re.escape(surface)))
        if rx.search(padded):
            return True
    # Also: explicit "polite past = ました" style.
    if re.search(rf"(form|ending|suffix|conjugation|past|polite|negative|volitional|progressive|desire)[^。\n]{{0,40}}{re.escape(surface)}", mainuse, re.IGNORECASE):
        return True
    return False


def is_contrastive_only(mainuse: str, surface: str) -> bool:
    """If every occurrence of `surface` in `mainuse` sits inside a contrast
    construction (`X vs Y`, `X ≠ Y`, `not Y`, `or Y`), the surface is being
    referenced as a *contrast* form rather than the form being taught — so
    its absence from JP is not necessarily a bug."""
    # Find all occurrences
    occurrences = []
    start = 0
    while True:
        i = mainuse.find(surface, start)
        if i < 0:
            break
        occurrences.append(i)
        start = i + 1
    if not occurrences:
        return False
    for i in occurrences:
        # Look at a window of ~25 chars on each side
        left = mainuse[max(0, i - 25):i]
        right = mainuse[i + len(surface):i + len(surface) + 25]
        contrast_left = re.search(r"\b(vs|or|use|instead of|not|≠)\b", left, re.IGNORECASE)
        contrast_right = re.search(r"\b(vs|or)\b", right, re.IGNORECASE)
        if not (contrast_left or contrast_right):
            return False  # at least one non-contrastive occurrence — keep flag
    return True


def read_recognition_rows(path: Path) -> Iterable[tuple[int, list[str]]]:
    with path.open("r", encoding="utf-8") as f:
        cols = None
        for lineno, raw in enumerate(f, 1):
            line = raw.rstrip("\n")
            if not line:
                continue
            if line.startswith("#columns:"):
                cols = line[len("#columns:"):].split("\t")
                continue
            if line.startswith("#"):
                continue
            parts = line.split("\t")
            yield lineno, parts


def detect_a1(root: Path) -> list[dict]:
    hits: list[dict] = []
    for path in sorted(root.rglob("*_recognition.tsv")):
        # Confirm column order
        col_idx = None
        with path.open("r", encoding="utf-8") as f:
            for raw in f:
                if raw.startswith("#columns:"):
                    cols = raw.rstrip("\n")[len("#columns:"):].split("\t")
                    try:
                        jp_i = cols.index("JP")
                        mu_i = cols.index("MainUse")
                    except ValueError:
                        col_idx = None
                        break
                    col_idx = (jp_i, mu_i)
                    break
        if col_idx is None:
            continue
        jp_i, mu_i = col_idx
        for lineno, parts in read_recognition_rows(path):
            if len(parts) <= max(jp_i, mu_i):
                continue
            jp = parts[jp_i]
            mu = parts[mu_i]
            for surface in SURFACES:
                if surface not in mu:
                    continue
                if not is_form_reference(mu, surface):
                    continue
                if surface in jp:
                    continue
                if is_contrastive_only(mu, surface):
                    continue
                # Any conjugational equivalent in JP -> not a drift.
                equivs = EQUIVALENTS.get(surface, [surface])
                if any(eq in jp for eq in equivs):
                    continue
                # Compound-context false positives (e.g. にしたがって).
                if any(ctx in jp for ctx in COMPOUND_CONTEXTS.get(surface, [])):
                    continue
                hits.append({
                    "path": str(path),
                    "line": lineno,
                    "jp": jp,
                    "mainuse": mu,
                    "surface": surface,
                })
                break  # one hit per row is enough
    return hits


def detect_a4(root: Path, a1_hits: list[dict]) -> list[dict]:
    """A4 — parity mirror: Recognition+Production share JP/MainUse pairs
    where A1 fires. Find Production rows whose Sample matches a flagged
    Recognition JP AND Why == MainUse."""
    a1_keys = {(h["path"], h["jp"], h["mainuse"], h["surface"]) for h in a1_hits}
    # Group A1 hits by slug directory (= same point folder).
    by_slug: dict[str, list[dict]] = {}
    for h in a1_hits:
        slug_key = Path(h["path"]).name.replace("_recognition.tsv", "")
        slug_dir = str(Path(h["path"]).parent) + "::" + slug_key
        by_slug.setdefault(slug_dir, []).append(h)

    extra: list[dict] = []
    for slug_dir, hits in by_slug.items():
        parent, _, slug = slug_dir.partition("::")
        prod_path = Path(parent) / f"{slug}_production.tsv"
        if not prod_path.exists():
            continue
        # Read production rows
        cols = None
        with prod_path.open("r", encoding="utf-8") as f:
            for raw in f:
                if raw.startswith("#columns:"):
                    cols = raw.rstrip("\n")[len("#columns:"):].split("\t")
                    break
        if not cols:
            continue
        try:
            sample_i = cols.index("Sample")
            why_i = cols.index("Why")
        except ValueError:
            continue
        prod_rows: list[tuple[int, str, str]] = []
        with prod_path.open("r", encoding="utf-8") as f:
            for lineno, raw in enumerate(f, 1):
                line = raw.rstrip("\n")
                if not line or line.startswith("#"):
                    continue
                parts = line.split("\t")
                if len(parts) <= max(sample_i, why_i):
                    continue
                prod_rows.append((lineno, parts[sample_i], parts[why_i]))
        for h in hits:
            for lineno, sample, why in prod_rows:
                if sample == h["jp"] and why == h["mainuse"]:
                    extra.append({
                        "path": str(prod_path),
                        "line": lineno,
                        "jp": sample,
                        "why": why,
                        "surface": h["surface"],
                        "mirrored_from": f"{h['path']}:{h['line']}",
                    })
    return extra


def main() -> int:
    a1 = detect_a1(ROOT)
    a4 = detect_a4(ROOT, a1)
    print(f"# A1 hits: {len(a1)}")
    for h in a1:
        print(f"{h['path']}:{h['line']}\tsurface={h['surface']}\tJP={h['jp']}\tMainUse={h['mainuse']}")
    print(f"\n# A4 mirrored hits: {len(a4)}")
    for h in a4:
        print(f"{h['path']}:{h['line']}\tsurface={h['surface']}\tmirror_of={h['mirrored_from']}\tSample={h['jp']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
