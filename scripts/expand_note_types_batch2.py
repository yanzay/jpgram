#!/usr/bin/env python3
"""
Batch-2 note-type expansion using point-tag row extraction.

Unlike batch-1 (filename-based), this script works when many points are
co-located in one TSV (e.g. 00-foundation/copula_recognition.tsv).
"""
from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
GRAMMAR = ROOT / "grammar"
AUDIT = ROOT / "research-reports/coverage_audit_report.json"

CLOZE_RE = re.compile(r"\{\{c\d+::([^:}]+)(?:::[^}]+)?\}\}")


def strip_cloze(text: str) -> str:
    return CLOZE_RE.sub(r"\1", text)


def parse_tsv(path: Path):
    lines = path.read_text(encoding="utf-8").splitlines()
    header = None
    rows = []
    for ln in lines:
        if ln.startswith("#columns:"):
            header = ln[len("#columns:") :].split("\t")
            continue
        if not ln or ln.startswith("#"):
            continue
        row = next(csv.reader([ln], delimiter="\t", quotechar='"'))
        if header and len(row) == len(header):
            rows.append(row)
    return header, rows


def detect_note_type(path: Path) -> str:
    stem = path.stem
    for nt in ("recognition", "production", "cloze", "contrast", "listening", "dictation"):
        if stem.endswith(f"_{nt}"):
            return nt
    return "unknown"


def deck_title(module: str, leaf: str) -> str:
    module_title = {
        "00-foundation": "00 - Foundation",
        "01-n5": "01 - N5 Grammar",
        "02-n4": "02 - N4 Grammar",
        "03-n3": "03 - N3 Grammar",
        "04-n2": "04 - N2 Grammar",
        "05-n1": "05 - N1 Grammar",
        "06-keigo": "06 - Keigo (Honorifics)",
        "07-casual": "07 - Casual / Spoken Forms",
        "08-slang": "08 - Slang & Internet Speech",
        "09-sfp-aizuchi": "09 - Sentence-Final Particles & Aizuchi",
        "10-onomatopoeia": "10 - Onomatopoeia",
        "11-classical": "11 - Classical / Literary Carryover",
        "12-beyond-n1": "12 - Beyond N1 (Idioms, Set Phrases, 四字熟語)",
        "13-l1": "13 - L1 Interference (per-language)",
    }.get(module, module)
    return f"Japanese Grammar::{module_title}::{leaf}"


def write_production(path: Path, module: str, rows: list[list[str]]) -> None:
    out = [
        "#separator:tab",
        "#html:true",
        "#columns:Prompt\tTarget\tReading\tSample\tWhy\tAudio\tTags",
        "#notetype:Production",
        f"#deck:{deck_title(module, 'Production')}",
        "#",
    ]
    for r in rows:
        cells = []
        for c in r:
            if any(ch in c for ch in ['\t', '"']):
                cells.append('"' + c.replace('"', '""') + '"')
            else:
                cells.append(c)
        out.append("\t".join(cells))
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def write_recognition(path: Path, module: str, rows: list[list[str]]) -> None:
    out = [
        "#separator:tab",
        "#html:true",
        "#columns:JP\tReading\tEN\tLabel\tFormula\tMainUse\tQuickCue\tContrast\tAudio\tTags",
        "#notetype:Recognition",
        f"#deck:{deck_title(module, 'Recognition')}",
        "#",
    ]
    for r in rows:
        cells = []
        for c in r:
            if any(ch in c for ch in ['\t', '"']):
                cells.append('"' + c.replace('"', '""') + '"')
            else:
                cells.append(c)
        out.append("\t".join(cells))
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def main() -> int:
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    sparse = audit["details"]["sparse_note_types"]

    # Build point-indexed source rows by note type.
    by_point: dict[str, dict[str, list[tuple[str, list[str], str]]]] = defaultdict(lambda: defaultdict(list))
    for path in GRAMMAR.rglob("*.tsv"):
        nt = detect_note_type(path)
        if nt not in {"recognition", "contrast", "cloze"}:
            continue
        header, rows = parse_tsv(path)
        if not header:
            continue
        tags_idx = len(header) - 1
        for row in rows:
            tags = row[tags_idx].split()
            points = [t[len("point:") :] for t in tags if t.startswith("point:")]
            modules = [t[len("module:") :] for t in tags if t.startswith("module:")]
            module = modules[0] if modules else path.parent.name
            for p in points:
                by_point[p][nt].append((module, row, str(path.relative_to(ROOT))))

    created = []
    skipped = []
    # process top 40 remaining for this batch
    for item in sparse[:40]:
        point = item["point_slug"]
        note_types = item["note_types"]
        if len(note_types) != 1:
            continue
        nt = note_types[0]
        source_rows = by_point.get(point, {}).get(nt, [])
        if not source_rows:
            skipped.append((point, "no-source-rows"))
            continue
        module = source_rows[0][0]
        if nt == "recognition":
            out_path = GRAMMAR / module / f"{point}_production.tsv"
            if out_path.exists():
                skipped.append((point, "target-exists"))
                continue
            out_rows = []
            for _, row, _ in source_rows:
                # Recognition schema:
                # JP Reading EN Label Formula MainUse QuickCue Contrast Audio Tags
                prompt = row[2] or row[3] or row[5]
                why = row[5] or row[6] or row[4]
                out_rows.append([prompt, row[0], row[1], row[0], why, row[8], row[9]])
            write_production(out_path, module, out_rows)
            created.append((point, "recognition->production", len(out_rows), str(out_path.relative_to(ROOT))))
        elif nt == "contrast":
            out_path = GRAMMAR / module / f"{point}_recognition.tsv"
            if out_path.exists():
                skipped.append((point, "target-exists"))
                continue
            out_rows = []
            for _, row, _ in source_rows:
                # Contrast schema:
                # JP OptionA OptionB Answer Why Tip Audio Tags
                jp = row[0].replace("___", row[3]) if "___" in row[0] else row[0]
                out_rows.append([jp, "", row[4], "contrast-derived", row[3], row[4], row[5], f"{row[1]} vs {row[2]}", row[6], row[7]])
            write_recognition(out_path, module, out_rows)
            created.append((point, "contrast->recognition", len(out_rows), str(out_path.relative_to(ROOT))))
        elif nt == "cloze":
            out_path = GRAMMAR / module / f"{point}_recognition.tsv"
            if out_path.exists():
                skipped.append((point, "target-exists"))
                continue
            out_rows = []
            for _, row, _ in source_rows:
                # Cloze schema:
                # Text Reading Hint Audio Tags
                # Reject whole-sentence cloze (entire JP is deleted — teaches nothing).
                plain = strip_cloze(row[0])
                if not plain.strip() or plain.strip() == row[0].strip():
                    continue
                out_rows.append(
                    [
                        strip_cloze(row[0]),
                        strip_cloze(row[1]),
                        row[2],
                        "cloze-derived",
                        row[2],
                        row[2],
                        row[2],
                        "",
                        row[3],
                        row[4],
                    ]
                )
            write_recognition(out_path, module, out_rows)
            created.append((point, "cloze->recognition", len(out_rows), str(out_path.relative_to(ROOT))))

    print(f"created={len(created)}")
    for c in created:
        print(f"{c[0]}\t{c[1]}\trows={c[2]}\t{c[3]}")
    print(f"skipped={len(skipped)}")
    for s in skipped[:50]:
        print(f"{s[0]}\t{s[1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
