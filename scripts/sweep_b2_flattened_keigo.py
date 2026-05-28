#!/usr/bin/env python3
"""Phase 7.5 sweep B2 — flattened keigo register.

Flags rows whose JP carries clear keigo markers but whose EN uses casual
contractions/idioms ('I'm', 'let's', 'gonna', etc.).
"""
from __future__ import annotations

import re
import sys
from typing import List, Tuple

sys.path.insert(0, "/Users/ograc/projects/jpgram/scripts")
from _sweep_common import iter_card_files, get_jp_en_pairs, CARD_SUFFIXES

KEIGO_PATTERNS = [
    re.compile(r"お[一-龯ぁ-んァ-ヴ]+になる"),
    re.compile(r"お[一-龯ぁ-んァ-ヴ]+します"),
    re.compile(r"お[一-龯ぁ-んァ-ヴ]+いたします"),
    re.compile(r"ご[一-龯]+いたします"),
    re.compile(r"ご[一-龯]+になる"),
    re.compile(r"申し上げ[るまれてた]"),
    re.compile(r"申します"),
    re.compile(r"させていただ[くきけ]"),
    re.compile(r"いたします"),
    re.compile(r"いただ[くけきい][^。、]"),  # avoid bare いた matching past
    re.compile(r"おっしゃ[るりっいい]"),
    re.compile(r"お越しになる"),
    re.compile(r"ご覧になる"),
    re.compile(r"お持ちする"),
    re.compile(r"でございます"),
    re.compile(r"ございます"),
]

CASUAL_PATTERNS = [
    re.compile(r"\bI'm\b"),
    re.compile(r"\bI've\b"),
    re.compile(r"\bI'd\b"),
    re.compile(r"\bI'll\b"),
    re.compile(r"\bwe're\b", re.IGNORECASE),
    re.compile(r"\bwe've\b", re.IGNORECASE),
    re.compile(r"\bwe'd\b", re.IGNORECASE),
    re.compile(r"\bwe'll\b", re.IGNORECASE),
    re.compile(r"\byou're\b", re.IGNORECASE),
    re.compile(r"\bthey're\b", re.IGNORECASE),
    re.compile(r"\blet's\b", re.IGNORECASE),
    re.compile(r"\bthat's\b", re.IGNORECASE),
    re.compile(r"\bhere's\b", re.IGNORECASE),
    re.compile(r"\bthere's\b", re.IGNORECASE),
    re.compile(r"\bit's\b", re.IGNORECASE),
    re.compile(r"\bstopped by\b", re.IGNORECASE),
    re.compile(r"\bdropped in\b", re.IGNORECASE),
    re.compile(r"\bgonna\b", re.IGNORECASE),
    re.compile(r"\bwanna\b", re.IGNORECASE),
    re.compile(r"\bc'mon\b", re.IGNORECASE),
]


def has_keigo(jp: str) -> List[str]:
    hits = []
    for p in KEIGO_PATTERNS:
        m = p.search(jp)
        if m:
            hits.append(m.group(0))
    return hits


def casual_hits(en: str) -> List[str]:
    hits = []
    for p in CASUAL_PATTERNS:
        m = p.search(en)
        if m:
            hits.append(m.group(0))
    return hits


def main() -> int:
    findings: List[Tuple[str, str, int, str, str, str, str, str]] = []
    total_keigo = 0
    for path in iter_card_files(CARD_SUFFIXES):
        for ln, jp, en, kind in get_jp_en_pairs(path):
            kei = has_keigo(jp)
            if not kei:
                continue
            total_keigo += 1
            cas = casual_hits(en)
            if not cas:
                continue
            findings.append((
                "HIGH", path, ln, kind, jp, en,
                ";".join(kei), ";".join(cas),
            ))

    findings.sort(key=lambda x: (x[1], x[2]))
    print(f"# B2 sweep — flattened keigo")
    print(f"# total keigo-bearing rows scanned: {total_keigo}")
    print(f"# HIGH findings: {len(findings)}")
    print()
    for sev, path, ln, kind, jp, en, kei, cas in findings:
        print(f"{sev}\t{path}\t{ln}\t{kind}\t{jp}\t{en}\t{kei}\t{cas}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
