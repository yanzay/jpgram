#!/usr/bin/env python3
"""
Phase-3 Track B — off-topic contrast files re-authored.

Each file gets 5 on-point fill-in-blank contrast rows with grammatically
parallel OptionA/B and a pedagogically meaningful contrast.

Schema: JP\tOptionA\tOptionB\tAnswer\tWhy\tTip\tAudio\tTags

Audio is empty + scaffold:pending-audio in tags (new sentences).
"""
from pathlib import Path

CONTENT = [
    {
        "path": "grammar-strict/02-n4/てもらう_contrast.tsv",
        "deck": "02 - N4",
        "module": "02-n4",
        "jlpt": "n4",
        "slug": "てもらう",
        "rows": [
            ("先生に教え___。", "てもらった", "てくれた", "てもらった",
             "てもらう = subject (me) receives the favor; てくれる = doer (teacher) gives the favor (to me)",
             "I-as-grammatical-subject → てもらう"),
            ("友達が手伝い___ので嬉しかった。", "てくれた", "てもらった", "てくれた",
             "てくれる = doer (friend) is the grammatical subject; てもらう would need 友達に, not 友達が",
             "doer-as-subject (が) → てくれる"),
            ("母にお弁当を作っ___。", "てもらった", "てくれた", "てもらった",
             "request-style: I had/got mother to prepare the bento; に marks the doer",
             "に + verb-doer → てもらう"),
            ("子供に絵本を読ん___。", "であげた", "でもらった", "であげた",
             "I read for the child (in-group → out-group favor); てあげる, not てもらう",
             "I do the favor → てあげる"),
            ("いつもサポートし___感謝しています。", "てくれて", "てもらって", "てくれて",
             "open-ended thanks to the doer (subject = doer); てくれる; てもらう would need a に-recipient frame",
             "thanking the doer → てくれる"),
        ],
    },
    {
        "path": "grammar-strict/02-n4/なさい_contrast.tsv",
        "deck": "02 - N4",
        "module": "02-n4",
        "jlpt": "n4",
        "slug": "なさい",
        "rows": [
            ("早く起き___。", "なさい", "ろ", "なさい",
             "なさい = mild firm directive (parent/teacher); ろ = rough imperative (peer/male)",
             "parent→child register → なさい"),
            ("静かに___。", "しなさい", "してください", "しなさい",
             "なさい directs the listener firmly; てください is a polite request to a peer/superior",
             "directive (top-down) → なさい"),
            ("宿題をやり___。", "なさい", "なよ", "なさい",
             "なさい = firm parent register; なよ = casual masculine command",
             "school context → なさい"),
            ("もっと真面目に勉強し___。", "なさい", "ろ", "なさい",
             "mild but firm correction from authority figure",
             "firm guidance → なさい"),
            ("ご飯を食べ___。", "なさい", "なよ", "なさい",
             "parent telling child to eat (firm, but not rough)",
             "parent-to-child meal-time → なさい"),
        ],
    },
    {
        "path": "grammar-strict/04-n2/にしたがって_contrast.tsv",
        "deck": "04 - N2",
        "module": "04-n2",
        "jlpt": "n2",
        "slug": "にしたがって",
        "rows": [
            ("年を取る___、考え方が変わる。", "にしたがって", "によって", "にしたがって",
             "にしたがって = gradual proportional change ('as X, then Y'); によって = means/agent ('by means of')",
             "gradual change → にしたがって"),
            ("規則___行動しなさい。", "にしたがって", "につれて", "にしたがって",
             "にしたがって also means 'in compliance with'; につれて only means gradual change",
             "compliance with rule → にしたがって"),
            ("高度が上がる___、気温が下がる。", "にしたがって", "ように", "にしたがって",
             "physical proportional relationship — gradual change",
             "physical law → にしたがって"),
            ("指示___、書類を提出した。", "にしたがって", "によって", "にしたがって",
             "compliance with instructions",
             "compliance with instruction → にしたがって"),
            ("経済発展___、生活が豊かになる。", "にしたがって", "としたら", "にしたがって",
             "gradual proportional improvement",
             "concurrent gradual change → にしたがって"),
        ],
    },
    {
        "path": "grammar-strict/04-n2/にもかかわらず_contrast.tsv",
        "deck": "04 - N2",
        "module": "04-n2",
        "jlpt": "n2",
        "slug": "にもかかわらず",
        "rows": [
            ("努力した___、結果が出なかった。", "にもかかわらず", "として", "にもかかわらず",
             "にもかかわらず = concessive 'despite/in spite of'; として = 'as/in the role of' (unrelated)",
             "despite — formal → にもかかわらず"),
            ("雨___、試合は予定通り行われた。", "にもかかわらず", "ながらも", "にもかかわらず",
             "にもかかわらず attaches to N directly; ながらも would need verb-stem or adjective",
             "N + concession → にもかかわらず"),
            ("高齢である___、彼は今も現役だ。", "にもかかわらず", "にしては", "にもかかわらず",
             "にもかかわらず = pure concession; にしては = 'considering that' (comparison)",
             "pure concession → にもかかわらず"),
            ("厳しい状況だ___、笑顔を絶やさない。", "にもかかわらず", "ようでは", "にもかかわらず",
             "concessive — strong contrast between situation and behaviour",
             "formal concession → にもかかわらず"),
            ("警告した___、彼は無視した。", "にもかかわらず", "ところで", "にもかかわらず",
             "concessive — warning ignored",
             "expectation violated → にもかかわらず"),
        ],
    },
    {
        "path": "grammar-strict/03-n3/とおり_contrast.tsv",
        "deck": "03 - N3",
        "module": "03-n3",
        "jlpt": "n3",
        "slug": "とおり",
        "rows": [
            ("説明の___やってください。", "とおり", "ように", "とおり",
             "とおり = exactly as / in the same way; ように = manner approximation ('in such a way that')",
             "literal sameness → とおり"),
            ("思った___結果が出た。", "とおり", "みたい", "とおり",
             "とおり = matches the prediction exactly",
             "as expected (exact) → とおり"),
            ("言われた___実行した。", "とおり", "より", "とおり",
             "とおり = followed instructions exactly",
             "exact compliance → とおり"),
            ("計画___進めよう。", "のとおり", "みたい", "のとおり",
             "Noun + のとおり; Adj/V-plain + ように; とおり needs の after noun",
             "N + の + とおり (literal)"),
            ("予想した___彼は来た。", "とおり", "ように", "とおり",
             "exact match between prediction and outcome",
             "predicted outcome — exact → とおり"),
        ],
    },
    {
        "path": "grammar-strict/03-n3/に違いない_contrast.tsv",
        "deck": "03 - N3",
        "module": "03-n3",
        "jlpt": "n3",
        "slug": "に違いない",
        "rows": [
            ("彼が犯人___。", "に違いない", "かもしれない", "に違いない",
             "に違いない = strong/certain inference; かもしれない = mere possibility",
             "speaker is certain → に違いない"),
            ("これは嘘___。", "に違いない", "のはずだ", "に違いない",
             "に違いない = subjective certainty; はずだ = logical expectation from known facts",
             "felt certainty → に違いない"),
            ("試験に合格した___。", "に違いない", "ようだ", "に違いない",
             "に違いない = strong assertion; ようだ = observation/appearance",
             "strong inference (past) → に違いない"),
            ("彼女は怒っている___。", "に違いない", "と思った", "に違いない",
             "に違いない is the speaker's current strong inference, not a past thought",
             "present strong inference → に違いない"),
            ("これは本物___。", "に違いない", "そうだ", "に違いない",
             "に違いない = certain; そうだ = hearsay or visual seeming",
             "speaker-asserted certainty → に違いない"),
        ],
    },
    {
        "path": "grammar-strict/03-n3/ということだ_contrast.tsv",
        "deck": "03 - N3",
        "module": "03-n3",
        "jlpt": "n3",
        "slug": "ということだ",
        "rows": [
            ("彼は今日来ない___。", "ということだ", "のだ", "ということだ",
             "ということだ = reporting hearsay; のだ = speaker's explanation",
             "second-hand report → ということだ"),
            ("つまり、賛成___。", "ということだ", "わけがない", "ということだ",
             "ということだ = summary/conclusion of preceding context",
             "summarising conclusion → ということだ"),
            ("試合は中止___。", "ということだ", "になる", "ということだ",
             "reporting an announced result vs predicting one",
             "announcement received → ということだ"),
            ("不正があった___。", "ということだ", "のだ", "ということだ",
             "hearsay vs personal explanation",
             "reporting indirect info → ということだ"),
            ("努力すれば成功する___。", "ということだ", "かもしれない", "ということだ",
             "moral / takeaway statement vs mere speculation",
             "drawn-out conclusion → ということだ"),
        ],
    },
    {
        "path": "grammar-strict/01-n5/どこ_contrast.tsv",
        "deck": "01 - N5",
        "module": "01-n5",
        "jlpt": "n5",
        "slug": "どこ",
        "rows": [
            ("トイレは___ですか。", "どこ", "どちら", "どこ",
             "どこ = neutral location query; どちら = polite/formal variant (also two-choice)",
             "neutral → どこ"),
            ("お住まいは___ですか。", "どちら", "どこ", "どちら",
             "どちら is the polite/honorific form of どこ for asking about a residence",
             "polite/formal → どちら"),
            ("___へ行きますか。", "どこ", "どっち", "どこ",
             "どこ + へ = direction interrogative; どっち is casual for two-option choice",
             "open direction → どこ"),
            ("___から来ましたか。", "どこ", "いつ", "どこ",
             "どこ = where (place); いつ = when (time) — different semantic class",
             "origin (place) → どこ"),
            ("家は___ですか。", "どこ", "どんな", "どこ",
             "どこ = location; どんな = what kind/quality — different question types",
             "asking location → どこ"),
        ],
    },
    {
        "path": "grammar-strict/03-n3/わけだ_contrast.tsv",
        "deck": "03 - N3",
        "module": "03-n3",
        "jlpt": "n3",
        "slug": "わけだ",
        "rows": [
            ("毎日練習している。だから上手になる___。", "わけだ", "はずだ", "わけだ",
             "わけだ = drawn conclusion from premise; はずだ = pure logical expectation",
             "follows-from-context → わけだ"),
            ("彼は5年も日本に住んでいた。道理で日本語が上手な___。", "わけだ", "ようだ", "わけだ",
             "わけだ confirms 'that makes sense / no wonder' from a stated cause",
             "no wonder → わけだ"),
            ("給料が下がった。家計が苦しくなる___。", "わけだ", "に違いない", "わけだ",
             "わけだ = logical consequence of the prior fact; ちがいない = strong inference",
             "consequential reasoning → わけだ"),
            ("つまり、私が間違っていた___。", "わけだ", "ものだ", "わけだ",
             "わけだ = arriving at the realisation; ものだ = general truth/exclamation",
             "drawn realisation → わけだ"),
            ("彼女は何度も練習した。だから自信がある___。", "わけだ", "だろう", "わけだ",
             "わけだ confirms a result that flows from a stated cause",
             "result-from-cause → わけだ"),
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
        path = Path(entry["path"])
        path.write_text(make_tsv(entry), encoding="utf-8")
        print(f"  WROTE {path}  ({len(entry['rows'])} rows)")
    print(f"\nTotal: {len(CONTENT)} contrast files re-authored.")


if __name__ == "__main__":
    main()
