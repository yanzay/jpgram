#!/usr/bin/env python3
"""Phase 7.5 sweep B1 — dropped ている continuous aspect.

Flags rows where JP ends in 〜ている。/〜ていた。/〜ています。/〜ていました。
but the paired EN lacks any English progressive/perfect marker.

Excludes stative verbs that natively map to simple present in English.

Outputs CSV-like report to stdout with columns:
  severity\tpath\tline\tkind\tjp\ten
"""
from __future__ import annotations

import re
import sys
from typing import List, Tuple

sys.path.insert(0, "/Users/ograc/projects/jpgram/scripts")
from _sweep_common import iter_card_files, get_jp_en_pairs, CARD_SUFFIXES

# JP must end with one of these (terminal punctuation tolerant).
TEIRU_TAIL = re.compile(
    r"(て|で)(い(ま)?す|い(ま)?した|る|た)([。.!?！？]|$)"
)
# Match 〜ている / 〜ていた / 〜ています / 〜ていました at end of JP cell.
# The いる/いた/etc. nucleus is mandatory — bare て+る/た is past tense, not ている.
TEIRU_END = re.compile(
    r"(て|で)(いる|いた|います|いました)([。.!?！？]|」|』)?\s*$"
)

# Stative stems whose native EN is simple present.
STATIVE_STEMS = [
    "知っ", "知り", "持っ", "住ん", "結婚し", "飛ん", "落ち",
    "太っ", "痩せ", "似", "愛し", "困っ", "悲しん", "怒っ",
    "分かっ", "すぐれ", "たっ", "決まっ", "違っ", "合っ",
    "要っ", "おっ", "信じ",
    # Extended: thought/feeling/perception verbs that also map to simple present.
    "思っ", "感じ", "考え", "覚え",
    # Desire form たがる: 〜たがっ
    "たがっ",
    # Idiomatic 顔をして / 格好をして → "looks" (verb is して but stem ends in を)
]

# Habitual-frequency adverbs in JP that justify EN simple present even with ている.
HABITUAL_ADVERBS = [
    "毎日", "毎朝", "毎晩", "毎週", "毎年", "毎月", "毎回",
    "いつも", "よく", "ふだん", "普段", "週末", "週末は",
    "たいてい", "大抵", "しょっちゅう", "常に", "日々",
]

# EN progressive / perfect markers.
# Match standalone words; -ing is matched as any word ending in 'ing'.
ING_RE = re.compile(r"\b[A-Za-z]+ing\b", re.IGNORECASE)
AUX_RE = re.compile(
    r"\b(?:was|were|is|are|am|been|has been|have been|had been)\b",
    re.IGNORECASE,
)
# "had" + past participle: approximate by 'had ' followed by a word ending in 'ed' or known irregulars.
HAD_PP_RE = re.compile(
    r"\bhad\s+[A-Za-z]+(?:ed|en|ne|wn|ung|own|orne|ought|aught)\b",
    re.IGNORECASE,
)
SOFT_PASS_RE = re.compile(
    r"\b(currently|right now|at the moment|these days|nowadays|presently)\b",
    re.IGNORECASE,
)


def jp_ends_with_teiru(jp: str) -> Tuple[bool, str]:
    """Return (matches, stem_before_teiru). Stem may be empty if not extractable."""
    m = TEIRU_END.search(jp)
    if not m:
        return False, ""
    # Strip trailing punctuation/quotes to find the stem before て|で.
    stripped = re.sub(r"[。.!?！？」』\s]+$", "", jp)
    # Drop the trailing いる/いた/います/いました.
    stripped = re.sub(r"(います|いました|いる|いた)$", "", stripped)
    if stripped.endswith("て") or stripped.endswith("で"):
        # Find a reasonable stem window (up to 4 chars before て|で).
        head = stripped[:-1]
        stem_window = head[-4:] if len(head) >= 4 else head
        return True, stem_window
    return False, ""


def is_stative(stem_window: str) -> bool:
    for s in STATIVE_STEMS:
        if stem_window.endswith(s):
            return True
    return False


def is_habitual(jp: str) -> bool:
    for adv in HABITUAL_ADVERBS:
        if adv in jp:
            return True
    return False


# Idiomatic 顔/格好/服装/様子 + をしている → "looks/wears" — not a continuous-aspect drop.
IDIOM_KAO_RE = re.compile(r"(顔|格好|服装|様子|形|姿)をして(い(ま)?(す|した)|る|た)")


def has_progressive_en(en: str) -> bool:
    if ING_RE.search(en):
        return True
    if AUX_RE.search(en):
        return True
    if HAD_PP_RE.search(en):
        return True
    return False


def main() -> int:
    findings: List[Tuple[str, str, int, str, str, str]] = []
    total_teiru = 0
    excluded_stative = 0
    excluded_habitual = 0
    excluded_idiom = 0
    soft_pass = 0

    for path in iter_card_files(CARD_SUFFIXES):
        # Skip contrast files (we don't include those in CARD_SUFFIXES, defensive).
        for ln, jp, en, kind in get_jp_en_pairs(path):
            matches, stem = jp_ends_with_teiru(jp)
            if not matches:
                continue
            total_teiru += 1
            if is_stative(stem):
                excluded_stative += 1
                continue
            if IDIOM_KAO_RE.search(jp):
                excluded_idiom += 1
                continue
            if is_habitual(jp):
                excluded_habitual += 1
                continue
            if has_progressive_en(en):
                continue
            if SOFT_PASS_RE.search(en):
                soft_pass += 1
                continue
            # Severity: HIGH unless EN very short (might be label-ish) -> still HIGH.
            findings.append(("HIGH", path, ln, kind, jp, en))

    findings.sort(key=lambda x: (x[1], x[2]))
    print(f"# B1 sweep — dropped ている", flush=True)
    print(f"# total ている-terminal rows scanned: {total_teiru}")
    print(f"# excluded as stative: {excluded_stative}")
    print(f"# excluded as habitual (毎日/いつも/etc.): {excluded_habitual}")
    print(f"# excluded as 顔/格好をして idiom: {excluded_idiom}")
    print(f"# soft-pass (adverbial continuity): {soft_pass}")
    print(f"# HIGH findings: {len(findings)}")
    print()
    for sev, path, ln, kind, jp, en in findings:
        print(f"{sev}\t{path}\t{ln}\t{kind}\t{jp}\t{en}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
