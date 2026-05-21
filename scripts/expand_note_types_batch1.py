#!/usr/bin/env python3
"""
Batch-1 note-type expansion for top priority single-type points.

Strategy:
- contrast-only point -> add recognition file
- cloze-only point -> add recognition file
- recognition-only point -> add production file

Inputs:
  - research-reports/coverage_remediation_backlog.json
  - grammar/**/*_{recognition,contrast,cloze}.tsv
"""
from __future__ import annotations

import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
GRAMMAR = ROOT / "grammar"
BACKLOG = ROOT / "research-reports/coverage_remediation_backlog.json"

CLOZE_RE = re.compile(r"\{\{c\d+::([^:}]+)(?:::[^}]+)?\}\}")


def strip_cloze(text: str) -> str:
    return CLOZE_RE.sub(r"\1", text)


def read_tsv(path: Path) -> tuple[list[str], list[list[str]], list[str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    meta = []
    header = []
    rows: list[list[str]] = []
    for ln in lines:
        if ln.startswith("#"):
            meta.append(ln)
            if ln.startswith("#columns:"):
                header = ln[len("#columns:") :].split("\t")
            continue
        if not ln:
            continue
        rows.append(next(csv.reader([ln], delimiter="\t", quotechar='"')))
    return meta, header, rows


def write_tsv(path: Path, meta: list[str], header: list[str], rows: list[list[str]]) -> None:
    out = []
    meta_out = []
    for m in meta:
        if m.startswith("#columns:"):
            continue
        if m.startswith("#notetype:"):
            continue
        if m.startswith("#deck:"):
            continue
        meta_out.append(m)
    out.extend(meta_out)
    out.append("#columns:" + "\t".join(header))
    note_type = "Recognition" if "JP" in header and "Label" in header else "Production"
    out.append(f"#notetype:{note_type}")

    # Deck path inherits module and switches leaf to note type.
    module = path.parent.name
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
    deck_leaf = "Recognition" if note_type == "Recognition" else "Production"
    out.append(f"#deck:Japanese Grammar::{module_title}::{deck_leaf}")
    out.append("#")

    for row in rows:
        cells = []
        for cell in row:
            if any(ch in cell for ch in ['\t', '"']):
                cells.append('"' + cell.replace('"', '""') + '"')
            else:
                cells.append(cell)
        out.append("\t".join(cells))
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def generate_recognition_from_contrast(src: Path, dst: Path) -> int:
    _, header, rows = read_tsv(src)
    idx = {k: i for i, k in enumerate(header)}
    out_rows: list[list[str]] = []
    for r in rows:
        jp = r[idx["JP"]]
        ans = r[idx["Answer"]]
        full_jp = jp.replace("___", ans) if "___" in jp else jp
        out_rows.append(
            [
                full_jp,
                "",
                r[idx["Why"]],
                "contrast-derived",
                ans,
                r[idx["Why"]],
                r[idx["Tip"]],
                f"{r[idx['OptionA']]} vs {r[idx['OptionB']]}",
                r[idx["Audio"]],
                r[idx["Tags"]],
            ]
        )
    write_tsv(
        dst,
        ["#separator:tab", "#html:true"],
        ["JP", "Reading", "EN", "Label", "Formula", "MainUse", "QuickCue", "Contrast", "Audio", "Tags"],
        out_rows,
    )
    return len(out_rows)


def generate_recognition_from_cloze(src: Path, dst: Path) -> int:
    _, header, rows = read_tsv(src)
    idx = {k: i for i, k in enumerate(header)}
    out_rows: list[list[str]] = []
    for r in rows:
        # Reject whole-sentence cloze (entire JP is deleted — teaches nothing).
        plain = strip_cloze(r[idx["Text"]])
        if plain.strip() == r[idx["Text"]].strip():
            continue  # no cloze marker at all — skip
        if not plain.strip():
            continue  # entire sentence is cloze content — skip
        out_rows.append(
            [
                strip_cloze(r[idx["Text"]]),
                strip_cloze(r[idx["Reading"]]),
                r[idx["Hint"]],
                "cloze-derived",
                r[idx["Hint"]],
                r[idx["Hint"]],
                r[idx["Hint"]],
                "",
                r[idx["Audio"]],
                r[idx["Tags"]],
            ]
        )
    write_tsv(
        dst,
        ["#separator:tab", "#html:true"],
        ["JP", "Reading", "EN", "Label", "Formula", "MainUse", "QuickCue", "Contrast", "Audio", "Tags"],
        out_rows,
    )
    return len(out_rows)


def generate_production_from_recognition(src: Path, dst: Path) -> int:
    _, header, rows = read_tsv(src)
    idx = {k: i for i, k in enumerate(header)}
    out_rows: list[list[str]] = []
    for r in rows:
        prompt = r[idx["EN"]] or r[idx["Label"]] or r[idx["MainUse"]]
        why = r[idx["MainUse"]] or r[idx["QuickCue"]] or r[idx["Formula"]]
        out_rows.append(
            [
                prompt,
                r[idx["JP"]],
                r[idx["Reading"]],
                r[idx["JP"]],
                why,
                r[idx["Audio"]],
                r[idx["Tags"]],
            ]
        )
    write_tsv(
        dst,
        ["#separator:tab", "#html:true"],
        ["Prompt", "Target", "Reading", "Sample", "Why", "Audio", "Tags"],
        out_rows,
    )
    return len(out_rows)


def find_single_source(point_slug: str) -> tuple[str, Path] | None:
    hits = []
    for nt in ("contrast", "cloze", "recognition"):
        p = next(iter(GRAMMAR.rglob(f"{point_slug}_{nt}.tsv")), None)
        if p and p.exists():
            hits.append((nt, p))
    return hits[0] if len(hits) == 1 else None


def main() -> int:
    data = __import__("json").loads(BACKLOG.read_text(encoding="utf-8"))
    top = data["priorities"]["note_type_expansion"][:20]
    created = []
    skipped = []
    for item in top:
        point = item["point_slug"]
        source = find_single_source(point)
        if not source:
            skipped.append((point, "no-single-source-found"))
            continue
        src_type, src_path = source
        if src_type == "contrast":
            dst = src_path.with_name(f"{point}_recognition.tsv")
            if dst.exists():
                skipped.append((point, "target-exists"))
                continue
            n = generate_recognition_from_contrast(src_path, dst)
            created.append((point, "contrast->recognition", n, str(dst.relative_to(ROOT))))
        elif src_type == "cloze":
            dst = src_path.with_name(f"{point}_recognition.tsv")
            if dst.exists():
                skipped.append((point, "target-exists"))
                continue
            n = generate_recognition_from_cloze(src_path, dst)
            created.append((point, "cloze->recognition", n, str(dst.relative_to(ROOT))))
        elif src_type == "recognition":
            dst = src_path.with_name(f"{point}_production.tsv")
            if dst.exists():
                skipped.append((point, "target-exists"))
                continue
            n = generate_production_from_recognition(src_path, dst)
            created.append((point, "recognition->production", n, str(dst.relative_to(ROOT))))

    print(f"created={len(created)}")
    for c in created:
        print(f"{c[0]}\t{c[1]}\trows={c[2]}\t{c[3]}")
    print(f"skipped={len(skipped)}")
    for s in skipped:
        print(f"{s[0]}\t{s[1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
