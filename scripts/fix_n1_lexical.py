#!/usr/bin/env python3
"""N1 native-pass lexical/grammar fixes — single-substring replacements
scoped to specific defective rows. Each tuple's wrong string is unique
enough to land only on the intended row."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "grammar-strict"

REPLACEMENTS = [
    # ながらに:10 領導者 → 指導者 (non-standard lexis)
    ("生まれながらにして領導者の資質を持つ人がいる", "生まれながらにして指導者の資質を持つ人がいる"),
    ("うまれながらにしてりょうどうしゃのししつをもつひとがいる", "うまれながらにしてしどうしゃのししつをもつひとがいる"),
    # ながらに:8 泣きながらに → 涙ながらに (marginal usage)
    ("泣きながらに事実を打ち明けた", "涙ながらに事実を打ち明けた"),
    ("なきながらにじじつをうちあけた", "なみだながらにじじつをうちあけた"),
    # わ-わで:9 不況のわ → 不況だわ (ungrammatical)
    ("不況のわ、競合が増えるわで、経営が難しい", "不況だわ、競合が増えるわで、経営が難しい"),
    ("ふきょうのわ、きょうごうがふえるわで、けいえいがむずかしい", "ふきょうだわ、きょうごうがふえるわで、けいえいがむずかしい"),
    # にして1:9 若くにして → 若くして (non-standard form)
    ("若くにして天才の片鱗を見せていた", "若くして天才の片鱗を見せていた"),
    ("わかくにしててんさいのへんりんをみせていた", "わかくしててんさいのへんりんをみせていた"),
    # べくして:7 なるべくしてこうなった → なるべくしてなった結果だ
    ("なるべくしてこうなった。", "なるべくしてなった結果だ。"),
    ("なるべくしてこうなった。", "なるべくしてなったけっかだ。"),  # reading - separate handled below
    # が早いか_production.tsv:10 火事報知機 → 火災報知機
    ("火事報知機", "火災報知機"),
    ("かじほうちき", "かさいほうちき"),
]


def fix_file(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    fixed = text
    hits = 0
    for wrong, right in REPLACEMENTS:
        if wrong in fixed:
            fixed = fixed.replace(wrong, right)
            hits += 1
    if fixed != text:
        path.write_text(fixed, encoding="utf-8")
    return hits


if __name__ == "__main__":
    total = 0
    files_changed = 0
    for tsv in sorted(ROOT.rglob("*.tsv")):
        n = fix_file(tsv)
        if n:
            total += n
            files_changed += 1
            print(f"{tsv.relative_to(ROOT.parent)}: {n} replacement(s)")
    print(f"\nTotal: {total} replacement(s) across {files_changed} file(s).")
