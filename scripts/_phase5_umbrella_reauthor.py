#!/usr/bin/env python3
"""
Phase-5 — focus the umbrella-slug files on their Bunpro-defined sense.

Bunpro's taxonomy defines a single sense per slug:
- と (N5)    = Quotation
- って (N5)  = Casual quotation
- まで (N4)  = Even / to the extent of

The existing TSVs taught wrong senses:
- と_*.tsv: conditional と (natural consequence) — that's a different Bunpro point
- って_*.tsv: te-form derivation drill — not a quotation in sight
- まで_*.tsv recognition: random sentences with no まで

This script re-authors recognition + production for each slug,
focused on the Bunpro-defined sense.
"""
from pathlib import Path

CONTENT = [
    # と — Bunpro: Quotation
    {
        "path_rec": "grammar-strict/01-n5/と_recognition.tsv",
        "path_prod": "grammar-strict/01-n5/と_production.tsv",
        "module": "01-n5", "jlpt": "n5", "slug": "と",
        "deck_rec": "01 - N5 Grammar::Recognition",
        "deck_prod": "01 - N5 Grammar::Production",
        "label": "と (quotation particle)",
        "formula": "[clause/word] + と + 言う / 思う / 書く",
        "contrast": "と = direct/indirect quotation; って = casual quotation; ように = manner approximation",
        "rows": [
            ("彼は来ないと言った。", "かれはこないといった。",
             "He said he wouldn't come.",
             "と + 言う: direct/indirect speech report",
             "report past speech"),
            ("田中さんは医者だと思います。", "たなかさんはいしゃだとおもいます。",
             "I think Tanaka is a doctor.",
             "と + 思う: report a thought / opinion",
             "stating opinion"),
            ("ここに名前を書いてくださいと言われました。", "ここになまえをかいてくださいといわれました。",
             "I was told 'please write your name here'.",
             "embedded request + と + 言われる: quoted instruction",
             "instruction received"),
            ("「明日会いましょう」と返事した。", "あしたあいましょうとへんじした。",
             "I replied, \"Let's meet tomorrow.\"",
             "direct quotation marker + と + 返事する",
             "reply quoted"),
            ("彼は無理だと諦めた。", "かれはむりだとあきらめた。",
             "He gave up, thinking it was impossible.",
             "と + 諦める: report internal acceptance",
             "giving up — quoted thought"),
        ],
    },
    # って — Bunpro: Casual quotation
    {
        "path_rec": "grammar-strict/01-n5/って_recognition.tsv",
        "path_prod": "grammar-strict/01-n5/って_production.tsv",
        "module": "01-n5", "jlpt": "n5", "slug": "って",
        "deck_rec": "01 - N5 Grammar::Recognition",
        "deck_prod": "01 - N5 Grammar::Production",
        "label": "って (casual quotation particle)",
        "formula": "[clause/word] + って (casual contraction of と)",
        "contrast": "って = casual; と = neutral; とは = topical/emphatic",
        "rows": [
            ("彼、来ないって。", "かれ、こないって。",
             "He says he isn't coming.",
             "って at sentence end: casual hearsay report",
             "reporting friend's word"),
            ("田中さんって誰？", "たなかさんってだれ？",
             "Who's this Tanaka person?",
             "Noun + って + question: casual definition request",
             "asking who someone is"),
            ("明日休みだって聞いたよ。", "あしたやすみだってきいたよ。",
             "I heard tomorrow is a day off.",
             "って + 聞いた: casual 'I heard that…'",
             "casual hearsay"),
            ("彼女、もう帰ったって。", "かのじょ、もうかえったって。",
             "She says she's already gone home.",
             "Sentence + って (sentence-final): conveying someone's words",
             "passing on info"),
            ("「ありがとう」って言われた。", "ありがとうっていわれた。",
             "I was told \"thank you.\"",
             "Direct quote + って + 言われる: casual report of speech received",
             "casual report"),
        ],
    },
    # まで — Bunpro: Even / to the extent of
    {
        "path_rec": "grammar-strict/02-n4/まで_recognition.tsv",
        "path_prod": "grammar-strict/02-n4/まで_production.tsv",
        "module": "02-n4", "jlpt": "n4", "slug": "まで",
        "deck_rec": "02 - N4 Grammar::Recognition",
        "deck_prod": "02 - N4 Grammar::Production",
        "label": "まで (even, to the extent of)",
        "formula": "N / Verb-plain + まで",
        "contrast": "まで = extreme extent; さえ = even (minimum case); だけ = only (limit)",
        "rows": [
            ("子供にまで笑われた。", "こどもにまでわらわれた。",
             "Even children laughed at me.",
             "まで: emphatic extent — extending to an unexpected target",
             "even children laughed"),
            ("そこまでしてくれなくてもいい。", "そこまでしてくれなくてもいい。",
             "You didn't have to go that far for me.",
             "そこまで: 'to that extent' — declining excessive favour",
             "appreciating, but declining"),
            ("夜中まで起きて勉強した。", "よなかまでおきてべんきょうした。",
             "I stayed up studying until the middle of the night.",
             "まで: temporal extent — until late",
             "studying late"),
            ("死ぬまで頑張ると約束した。", "しぬまでがんばるとやくそくした。",
             "I promised I'd work my hardest until I die.",
             "Verb + まで: extreme limit of commitment",
             "lifelong commitment"),
            ("親にまで嘘をついた。", "おやにまでうそをついた。",
             "I even lied to my parents.",
             "にまで: 'even to' — emphasising the unexpected target",
             "betrayal of trust"),
        ],
    },
]


def make_recognition(entry):
    deck = f"Japanese Grammar::{entry['deck_rec']}"
    header = (
        "#separator:tab\n"
        "#html:true\n"
        "#columns:JP\tReading\tEN\tLabel\tFormula\tMainUse\tQuickCue\tContrast\tAudio\tTags\n"
        "#notetype:Recognition\n"
        f"#deck:{deck}\n"
        "\n"
    )
    body = []
    for jp, reading, en, mainuse, quickcue in entry["rows"]:
        tags = (
            f"module:{entry['module']} jlpt:{entry['jlpt']} point:{entry['slug']} "
            f"complexity:standard source:authored frequency:top10k scaffold:pending-audio"
        )
        body.append(
            f"{jp}\t{reading}\t{en}\t{entry['label']}\t{entry['formula']}\t"
            f"{mainuse}\t{quickcue}\t{entry['contrast']}\t\t{tags}\n"
        )
    return header + "".join(body)


def make_production(entry):
    deck = f"Japanese Grammar::{entry['deck_prod']}"
    header = (
        "#separator:tab\n"
        "#html:true\n"
        "#columns:Prompt\tTarget\tReading\tSample\tWhy\tAudio\tTags\n"
        "#notetype:Production\n"
        f"#deck:{deck}\n"
        "\n"
    )
    body = []
    for jp, reading, en, mainuse, _ in entry["rows"]:
        tags = (
            f"module:{entry['module']} jlpt:{entry['jlpt']} point:{entry['slug']} "
            f"complexity:standard source:authored frequency:top10k scaffold:pending-audio"
        )
        body.append(
            f"{en}\t{entry['slug']}\t{reading}\t{jp}\t{mainuse}\t\t{tags}\n"
        )
    return header + "".join(body)


def main():
    for entry in CONTENT:
        Path(entry["path_rec"]).write_text(make_recognition(entry), encoding="utf-8")
        Path(entry["path_prod"]).write_text(make_production(entry), encoding="utf-8")
        print(f"  WROTE {entry['slug']}_recognition + production")


if __name__ == "__main__":
    main()
