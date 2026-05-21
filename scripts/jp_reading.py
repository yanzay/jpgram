#!/usr/bin/env python3
"""
Context-aware hiragana reading for grammar TSV authoring.

fugashi (+ UniDic-Lite) gives accurate token-level kana most of the time;
this module adds overrides for compounds where the UniDic default is wrong
in everyday text (今日 → きょう, not こんにち; お母さん → おかあさん, etc.),
a numeral/symbol transliterator (100℃ → ひゃくど), and a validation helper
that rejects malformed readings (sokuon doubling, bare kanji, etc.).
"""
from __future__ import annotations

import re
from typing import Iterable

import jaconv
from fugashi import Tagger

# ── Numeral transliteration ──────────────────────────────────────────────────

_ONES = ["", "いち", "に", "さん", "よん", "ご", "ろく", "なな", "はち", "きゅう"]
_JUUS = ["", "じゅう", "にじゅう", "さんじゅう", "よんじゅう", "ごじゅう",
         "ろくじゅう", "ななじゅう", "はちじゅう", "きゅうじゅう"]
_HUNDREDS = ["", "ひゃく", "にひゃく", "さんびゃく", "よんひゃく", "ごひゃく",
             "ろっぴゃく", "ななひゃく", "はっぴゃく", "きゅうひゃく"]
_THOUSANDS = ["", "せん", "にせん", "さんぜん", "よんせん", "ごせん",
              "ろくせん", "ななせん", "はっせん", "きゅうせん"]


def _num2kana(n: int) -> str:
    """Positive integer → standard Japanese reading stem (no counter suffix)."""
    if n == 0:
        return "ぜろ"
    parts: list[str] = []
    if n >= 100_000_000:
        oku, n = divmod(n, 100_000_000)
        parts.append(_num2kana(oku) + "おく")
    if n >= 10_000:
        man, n = divmod(n, 10_000)
        parts.append(_num2kana(man) + "まん")
    if n >= 1_000:
        sen, n = divmod(n, 1_000)
        parts.append(_THOUSANDS[sen])  # _THOUSANDS[1]="せん" (not いちせん)
    if n >= 100:
        hyaku, n = divmod(n, 100)
        parts.append(_HUNDREDS[hyaku])  # _HUNDREDS[1]="ひゃく" (not いちひゃく)
    if n >= 10:
        ju, n = divmod(n, 10)
        parts.append(_JUUS[ju])  # _JUUS[1]="じゅう" (not いちじゅう)
    if n >= 1:
        parts.append(_ONES[n])
    return "".join(parts)


# Clock-time hours with irregular readings (4時=よじ, 7時=しちじ, 9時=くじ).
_CLOCK_OVERRIDES: dict[int, str] = {4: "よ", 7: "しち", 9: "く"}


def _clock_hour_kana(n: int) -> str:
    return _CLOCK_OVERRIDES.get(n, _num2kana(n))


def _minutes_reading(n: int) -> str:
    """Convert n to its X分 hiragana reading (ふん or ぷん with gemination)."""
    base = _num2kana(n)
    d = n % 10
    # Gemination: 1,6,8 → っぷん; 3,4 → ぷん; multiples of 10 → じゅっぷん
    if d == 1 and base.endswith("いち"):
        return base[:-2] + "いっぷん"
    if d == 6 and base.endswith("ろく"):
        return base[:-2] + "ろっぷん"
    if d == 8 and base.endswith("はち"):
        return base[:-2] + "はっぷん"
    if d in (3, 4):
        return base + "ぷん"
    if d == 0:
        if base.endswith("じゅう"):
            return base[:-3] + "じゅっぷん"
        if base.endswith("ひゃく"):
            return base[:-3] + "ひゃっぷん"
    return base + "ふん"


def _age_reading(n: int) -> str:
    """Convert n to its X歳 hiragana reading."""
    if n == 20:
        return "はたち"
    base = _num2kana(n)
    d = n % 10
    if d == 1 and base.endswith("いち"):
        return base[:-2] + "いっさい"
    if d == 8 and base.endswith("はち"):
        return base[:-2] + "はっさい"
    return base + "さい"


# One-pass regex: handles the most common digit+unit patterns.
# Order matters inside the alternation (longer/more-specific first).
_NUM_UNIT_RE = re.compile(
    r"(\d+)"
    r"(?:"
    r"(万円)"        # 1万円 → いちまんえん
    r"|(円)"         # 500円 → ごひゃくえん
    r"|(時)"         # 7時 → しちじ
    r"|(分)"         # 30分 → さんじゅっぷん
    r"|(歳)"         # 18歳 → じゅうはっさい
    r"|([℃°]C?)"    # 100℃ → ひゃくど
    r")"
)


def _transliterate_numerals(text: str) -> str:
    """Replace digit+unit patterns with hiragana before tokenization."""
    def _replace(m: re.Match) -> str:
        n = int(m.group(1))
        if m.group(2):   return _num2kana(n) + "まんえん"
        if m.group(3):   return _num2kana(n) + "えん"
        if m.group(4):   return _clock_hour_kana(n) + "じ"
        if m.group(5):   return _minutes_reading(n)
        if m.group(6):   return _age_reading(n)
        if m.group(7):   return _num2kana(n) + "ど"
        return m.group(0)
    return _NUM_UNIT_RE.sub(_replace, text)


# ── Override tables ──────────────────────────────────────────────────────────

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
    # Personal pronouns / high-frequency nouns (UniDic defaults are wrong)
    "彼女": "かのじょ",
    "お金": "おかね",           # UniDic: おきん (Sino-Japanese reading)
    "外国人": "がいこくじん",
    "若き日": "わかきひ",
    # Clock-time hours that evade the numeral transliterator (kanji numerals)
    "七時": "しちじ", "八時": "はちじ", "九時": "くじ", "四時": "よじ",
    # Compound idioms / literary set phrases
    "や否や": "やいなや",
    "然くして": "しかくして",
    # Transitive/intransitive pairs: override to everyday spoken reading
    "開ける": "あける",    # UniDic may give ひらける
    "熱する": "ねっする",  # UniDic: ねつする (undoubled ラ行五段 form)
}

# Standalone-token fallbacks (UniDic returns the formal/older form by default).
TOKEN_OVERRIDES: dict[str, str] = {
    "私": "わたし",
    "今": "いま",
    "何": "なに",
    # Personal pronouns
    "彼": "かれ",     # UniDic: かの (literary/demonstrative reading)
    "親": "おや",     # UniDic: したし or しん
    "君": "きみ",     # UniDic: くん (honorific suffix reading)
    # Idiomatic verb reading: standard speech always いう, never ゆう
    "言う": "いう",
    "言った": "いった",
    "言って": "いって",
    "言います": "いいます",
    "言いました": "いいました",
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
    text = _transliterate_numerals(text)
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
    result = "".join(out)
    # Final sweep: any residual Arabic digits not caught by _transliterate_numerals
    # (e.g. units like 個, 割, キロ, 年代 not in the pattern table) → kana stems.
    result = _BARE_DIGIT_RE.sub(lambda m: _num2kana(int(m.group())), result)
    return result


# ── Validation helper ────────────────────────────────────────────────────────

_BARE_DIGIT_RE = re.compile(r"\d+")

_KANJI_RE = re.compile(r"[一-龯]")
_DIGIT_RE = re.compile(r"[0-9０-９]")
_SYMBOL_RE = re.compile(r"[℃°]")
_SOKUON_DOUBLE_RE = re.compile(r"っっ|ーー|ゅゅ|ょょ|ゃゃ")


def bad_reading_issues(r: str) -> list[str]:
    """Return a list of defect descriptions for a Reading column value, or [] if clean."""
    issues: list[str] = []
    if _KANJI_RE.search(r):
        issues.append("contains kanji")
    if _DIGIT_RE.search(r):
        issues.append("contains Arabic digits")
    if _SYMBOL_RE.search(r):
        issues.append("contains ℃/° symbol")
    m = _SOKUON_DOUBLE_RE.search(r)
    if m:
        issues.append(f"sokuon doubling: {m.group()!r}")
    return issues


def readings(texts: Iterable[str]) -> list[str]:
    return [reading(t) for t in texts]


if __name__ == "__main__":
    import sys
    for line in (sys.stdin if not sys.argv[1:] else sys.argv[1:]):
        line = line.rstrip("\n") if isinstance(line, str) else line
        print(reading(line))
