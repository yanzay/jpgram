#!/usr/bin/env python3
"""
Context-aware hiragana reading for grammar TSV authoring.

fugashi (+ UniDic-Lite) gives accurate token-level kana most of the time;
this module adds a small N5/N4 override layer for compounds where the
UniDic default is wrong in everyday text (今日 → きょう, not こんにち;
お母さん → おかあさん, etc.).
"""
from __future__ import annotations

from typing import Iterable

import jaconv
from fugashi import Tagger

# Multi-token phrase overrides (matched against consecutive token surfaces).
PHRASE_OVERRIDES: dict[str, str] = {
    # 何 + counters / time-words
    "何人": "なんにん", "何時": "なんじ", "何回": "なんかい", "何日": "なんにち",
    "何月": "なんがつ", "何年": "なんねん", "何歳": "なんさい", "何個": "なんこ",
    "何枚": "なんまい", "何番": "なんばん", "何度": "なんど", "何曜日": "なんようび",
    "何分": "なんぷん", "何時間": "なんじかん",
    # 〇〇さん family terms (UniDic gives 母→はは standalone)
    "お母さん": "おかあさん", "お父さん": "おとうさん",
    "お兄さん": "おにいさん", "お姉さん": "おねえさん",
    "お祖母さん": "おばあさん", "お祖父さん": "おじいさん",
    # Time words UniDic resolves to literary/formal kana
    "今日": "きょう", "昨日": "きのう", "明日": "あした",
    "明後日": "あさって", "一昨日": "おととい",
    "今朝": "けさ", "今晩": "こんばん", "今夜": "こんや",
    "今年": "ことし", "去年": "きょねん", "来年": "らいねん",
    # Counters / number compounds
    "一人": "ひとり", "二人": "ふたり",
    "一日": "いちにち", "一日中": "いちにちじゅう",
    "一回": "いっかい", "一度": "いちど", "一番": "いちばん",
    "一緒": "いっしょ", "一週間": "いっしゅうかん",
    # 日本 family
    "日本": "にほん", "日本語": "にほんご", "日本人": "にほんじん",
    # Other N5/N4 quirks
    "大人": "おとな", "子供": "こども",
    "上手": "じょうず", "下手": "へた",
    "大丈夫": "だいじょうぶ",
    "綺麗": "きれい", "好き": "すき", "嫌い": "きらい",
    "可愛い": "かわいい",
    "色々": "いろいろ", "色んな": "いろんな",
}

# Standalone-token fallbacks (UniDic returns the formal/older form by default).
TOKEN_OVERRIDES: dict[str, str] = {
    "私": "わたし",
    "今": "いま",
    "何": "なに",
}

_PHRASES_BY_LEN = sorted(PHRASE_OVERRIDES.items(), key=lambda kv: -len(kv[0]))

_TAGGER: Tagger | None = None


def _tagger() -> Tagger:
    global _TAGGER
    if _TAGGER is None:
        _TAGGER = Tagger()
    return _TAGGER


def _match_phrase(surfs: list[str], start: int) -> tuple[str, int] | None:
    """Return (kana, end_index_exclusive) if any phrase override matches starting at `start`."""
    for phrase, kana in _PHRASES_BY_LEN:
        acc = ""
        j = start
        while j < len(surfs) and len(acc) < len(phrase):
            acc += surfs[j]
            j += 1
            if acc == phrase:
                return kana, j
            if not phrase.startswith(acc):
                break
    return None


def reading(text: str) -> str:
    """Return the hiragana reading for a Japanese sentence."""
    tagger = _tagger()
    toks = list(tagger(text))
    surfs = [w.surface for w in toks]
    out: list[str] = []
    i = 0
    while i < len(toks):
        hit = _match_phrase(surfs, i)
        if hit is not None:
            kana, j = hit
            out.append(kana)
            i = j
            continue
        w = toks[i]
        if w.surface in TOKEN_OVERRIDES:
            out.append(TOKEN_OVERRIDES[w.surface])
            i += 1
            continue
        kana = w.feature.kana
        out.append(jaconv.kata2hira(kana) if kana else w.surface)
        i += 1
    return "".join(out)


def readings(texts: Iterable[str]) -> list[str]:
    return [reading(t) for t in texts]


if __name__ == "__main__":
    import sys
    for line in (sys.stdin if not sys.argv[1:] else sys.argv[1:]):
        line = line.rstrip("\n") if isinstance(line, str) else line
        print(reading(line))
