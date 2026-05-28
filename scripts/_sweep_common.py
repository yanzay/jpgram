"""Shared helpers for Phase 7.5 sweeps B1–B3."""
from __future__ import annotations

import os
from typing import Iterator, List, Tuple, Dict

DECK_ROOT = "/Users/ograc/projects/jpgram/grammar-strict"


def iter_card_files(suffixes: Tuple[str, ...]) -> Iterator[str]:
    """Yield absolute paths of TSV files matching given suffixes under DECK_ROOT."""
    for dirpath, _, files in os.walk(DECK_ROOT):
        for f in files:
            for s in suffixes:
                if f.endswith(s):
                    yield os.path.join(dirpath, f)
                    break


def parse_tsv(path: str) -> Tuple[List[str], List[Tuple[int, List[str]]]]:
    """Parse a TSV file. Returns (columns, rows_with_lineno).

    rows_with_lineno entries are (1-based line number in file, list of cells).
    Header lines starting with '#' and blank lines are skipped.
    """
    columns: List[str] = []
    rows: List[Tuple[int, List[str]]] = []
    with open(path, "r", encoding="utf-8") as fh:
        for i, line in enumerate(fh, start=1):
            raw = line.rstrip("\n")
            if not raw.strip():
                continue
            if raw.startswith("#"):
                if raw.startswith("#columns:"):
                    cols = raw[len("#columns:") :].strip()
                    columns = [c.strip() for c in cols.split("\t")]
                continue
            cells = raw.split("\t")
            rows.append((i, cells))
    return columns, rows


def cell(row: List[str], cols: List[str], name: str) -> str:
    """Return the cell value for a given column name, or '' if absent."""
    try:
        idx = cols.index(name)
    except ValueError:
        return ""
    if idx >= len(row):
        return ""
    return row[idx]


def get_jp_en_pairs(path: str) -> List[Tuple[int, str, str, str]]:
    """Return (lineno, jp, en, card_kind) tuples for every translatable row in path.

    card_kind in {recognition, production, dictation, listening}.
    Contrast files are intentionally skipped by the caller (filter on filename).
    """
    cols, rows = parse_tsv(path)
    pairs: List[Tuple[int, str, str, str]] = []
    fname = os.path.basename(path)
    if fname.endswith("_recognition.tsv"):
        kind = "recognition"
        jp_col, en_col = "JP", "EN"
    elif fname.endswith("_production.tsv"):
        kind = "production"
        jp_col, en_col = "Sample", "Prompt"
    elif fname.endswith("_dictation.tsv"):
        kind = "dictation"
        # Use Answer (full JP) over Prompt (cloze).
        jp_col = "Answer" if "Answer" in cols else "Prompt"
        en_col = "EN"
    elif fname.endswith("_listening.tsv"):
        kind = "listening"
        jp_col = "Transcript" if "Transcript" in cols else "JP"
        en_col = "EN"
    else:
        return []
    for ln, row in rows:
        jp = cell(row, cols, jp_col)
        en = cell(row, cols, en_col)
        if jp and en:
            pairs.append((ln, jp, en, kind))
    return pairs


CARD_SUFFIXES = (
    "_recognition.tsv",
    "_production.tsv",
    "_dictation.tsv",
    "_listening.tsv",
)
