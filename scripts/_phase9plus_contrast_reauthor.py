#!/usr/bin/env python3
"""
Re-author 3 contrast files left zero/near-zero on-topic by the trim wave:
- 04-n2/かねる_contrast.tsv
- 05-n1/のなんのって_contrast.tsv
- 02-n4/かしら_contrast.tsv
"""
from pathlib import Path

CONTENT = [
    {
        "path": "grammar-strict/04-n2/かねる_contrast.tsv",
        "deck": "04 - N2", "module": "04-n2", "jlpt": "n2", "slug": "かねる",
        "rows": [
            ("申し訳ございませんが、ご質問にはお答え___。", "しかねます", "しかねません",
             "しかねます",
             "かねる = unable to bring oneself to do; かねない = something undesirable might happen",
             "polite refusal → かねる"),
            ("そのような結論は、私には判断___。", "しかねます", "できません",
             "しかねます",
             "かねる = formal/humble inability; できない = neutral inability",
             "formal humble refusal → かねる"),
            ("油断していると、大事故にもなり___。", "かねない", "かねる",
             "かねない",
             "かねない = liable to happen (undesirable); かねる = unable to do",
             "undesirable possibility → かねない"),
            ("お引き受け___ご依頼で、申し訳ありません。", "しかねる", "しがたい",
             "しかねる",
             "しかねる + N: attributive 'a request one cannot accept'; しがたい = hard to do",
             "polite-refusal attribute → しかねる"),
            ("この問題は一人では解決し___。", "かねます", "かねません",
             "かねます",
             "かねます = humble form of かねる; ません ≠ かねません (different polarity)",
             "humble inability → かねます"),
        ],
    },
    {
        "path": "grammar-strict/05-n1/のなんのって_contrast.tsv",
        "deck": "05 - N1", "module": "05-n1", "jlpt": "n1", "slug": "のなんのって",
        "rows": [
            ("試験が難しい___、頭が痛くなった。", "のなんのって", "ほどに",
             "のなんのって",
             "のなんのって = vivid colloquial emphasis on extreme degree; ほどに = formal degree",
             "colloquial extreme → のなんのって"),
            ("混雑している___、電車に乗れなかった。", "のなんのって", "から",
             "のなんのって",
             "のなんのって stresses an over-the-top degree, from which the consequence follows",
             "extreme crowding → のなんのって"),
            ("彼の話が長い___、皆あくびをしていた。", "のなんのって", "ところが",
             "のなんのって",
             "のなんのって: speaker conveys exasperation at how extreme X was",
             "exasperated complaint → のなんのって"),
            ("料理が辛い___、汗が止まらなかった。", "のなんのって", "ばかりに",
             "のなんのって",
             "のなんのって = vivid extreme; ばかりに = causal 'just because'",
             "vivid degree → のなんのって"),
            ("仕事が忙しい___、休みが取れない。", "のなんのって", "あまり",
             "のなんのって",
             "のなんのって vs あまり: のなんのって is colloquial-vivid; あまり is more bookish",
             "colloquial 'so much that' → のなんのって"),
        ],
    },
    {
        "path": "grammar-strict/02-n4/かしら_contrast.tsv",
        "deck": "02 - N4", "module": "02-n4", "jlpt": "n4", "slug": "かしら",
        "rows": [
            ("明日は雨が降る___。", "かしら", "かな",
             "かしら",
             "かしら = feminine 'I wonder'; かな = gender-neutral / casual male",
             "feminine speaker → かしら"),
            ("彼は本当に来る___。", "かしら", "だろうか",
             "かしら",
             "かしら = soft feminine speculation; だろうか = formal speculation",
             "soft feminine doubt → かしら"),
            ("これでうまくいく___。", "かしら", "わよ",
             "かしら",
             "かしら = uncertain wondering; わよ = strong feminine assertion (no doubt)",
             "uncertainty (feminine) → かしら"),
            ("どうしたらいい___。", "かしら", "の",
             "かしら",
             "かしら = sole speculation; の = explanation-seeking question",
             "speculation about own action → かしら"),
            ("何時に来る___、ご存知ですか。", "かしら", "ですか",
             "かしら",
             "かしら mixed with です-form indicates soft polite-feminine wonder",
             "polite-feminine wonder → かしら"),
        ],
    },
]


def make_tsv(entry):
    deck = f"Japanese Grammar::{entry['deck']} Grammar::Contrast"
    header = (
        "#separator:tab\n"
        "#html:true\n"
        "#columns:JP\tOptionA\tOptionB\tAnswer\tWhy\tTip\tAudio\tTags\n"
        "#notetype:Contrast\n"
        f"#deck:{deck}\n"
        "\n"
    )
    body = []
    for jp, a, b, ans, why, tip in entry["rows"]:
        tags = (
            f"module:{entry['module']} "
            f"jlpt:{entry['jlpt']} "
            f"point:{entry['slug']} "
            f"complexity:standard "
            f"source:authored "
            f"frequency:top10k "
            f"scaffold:pending-audio"
        )
        body.append(f"{jp}\t{a}\t{b}\t{ans}\t{why}\t{tip}\t\t{tags}\n")
    return header + "".join(body)


def main():
    for entry in CONTENT:
        Path(entry["path"]).write_text(make_tsv(entry), encoding="utf-8")
        print(f"  WROTE {Path(entry['path']).name}  ({len(entry['rows'])} rows)")


if __name__ == "__main__":
    main()
