#!/usr/bin/env python3
"""
Phase-8 — re-author critical dictation + listening pairs.

The 2026-05-19 audit flagged 7 pairs where the existing content tests
unrelated grammar points (e.g., べき_dictation.tsv rows 16-23 drill
できます / てもいいです / つもりです / だろう / etc.). This generator
replaces each pair with 5 on-point exemplars.

Schemas (verified against grammar-strict/ headers):
  Dictation: Audio\tPrompt\tAnswer\tReading\tEN\tTags
    Prompt = JP sentence with the target form replaced by ___
    Answer = the target form (what the learner types after hearing audio)
    Reading = full kana of the complete sentence
    EN = full translation
  Listening: Audio\tTranscript\tReading\tEN\tHint\tTags
    Transcript = full JP sentence (no blank)
    Reading = full kana
    EN = full translation
    Hint = 2-4 word semantic cue (situation/topic)

Audio is empty + scaffold:pending-audio in tags.
"""
from pathlib import Path

# (slug, jlpt, module, deck-name-fragment, [ (transcript, target_form, reading, en, hint) ])
PAIRS = [
    {
        "slug": "べき",
        "jlpt": "n3",
        "module": "03-n3",
        "deck": "03 - N3",
        "rows": [
            ("学生はもっと勉強するべきだ。", "するべき",
             "がくせいはもっとべんきょうするべきだ。",
             "Students should study more.", "moral advice — study"),
            ("約束は守るべきだ。", "守るべき",
             "やくそくはまもるべきだ。",
             "One should keep promises.", "moral rule — promises"),
            ("そんなことを言うべきではない。", "言うべきではない",
             "そんなことをいうべきではない。",
             "You shouldn't say such things.", "negative obligation"),
            ("早めに連絡するべきだった。", "するべきだった",
             "はやめにれんらくするべきだった。",
             "I should have contacted them earlier.", "past regret"),
            ("これは検討するべき問題だ。", "するべき",
             "これはけんとうするべきもんだいだ。",
             "This is a matter that should be considered.", "deliberative obligation"),
        ],
    },
    {
        "slug": "とばかり",
        "jlpt": "n1",
        "module": "05-n1",
        "deck": "05 - N1",
        "rows": [
            ("文句があるんだ、とばかりにこちらをにらんでいた。", "とばかりに",
             "もんくがあるんだ、とばかりにこちらをにらんでいた。",
             "He was glaring at me as if to say 'I've got complaints'.", "glaring complaint"),
            ("聞いていないよ、とばかりに首を振った。", "とばかりに",
             "きいていないよ、とばかりにくびをふった。",
             "He shook his head as if to say 'I'm not listening'.", "shaking head"),
            ("早く帰れ、とばかりにドアを指さした。", "とばかりに",
             "はやくかえれ、とばかりにどあをゆびさした。",
             "He pointed at the door as if to say 'Get out'.", "pointing at door"),
            ("当然だ、とばかりに胸を張った。", "とばかりに",
             "とうぜんだ、とばかりにむねをはった。",
             "He puffed out his chest as if to say 'Of course'.", "proud posture"),
            ("分かっている、とばかりにうなずいた。", "とばかりに",
             "わかっている、とばかりにうなずいた。",
             "He nodded as if to say 'I understand'.", "knowing nod"),
        ],
    },
    {
        "slug": "とされている",
        "jlpt": "n4",
        "module": "02-n4",
        "deck": "02 - N4",
        "rows": [
            ("富士山は日本一の山とされている。", "とされている",
             "ふじさんはにほんいちのやまとされている。",
             "Mt. Fuji is regarded as Japan's foremost mountain.", "general regard"),
            ("この本は名作とされている。", "とされている",
             "このほんはめいさくとされている。",
             "This book is considered a masterpiece.", "literary judgment"),
            ("砂糖は健康に悪いとされている。", "とされている",
             "さとうはけんこうにわるいとされている。",
             "Sugar is said to be bad for health.", "health claim"),
            ("この遺跡は江戸時代に作られたとされている。", "とされている",
             "このいせきはえどじだいにつくられたとされている。",
             "This ruin is said to have been built in the Edo period.", "historical attribution"),
            ("この方法が最も効果的とされている。", "とされている",
             "このほうほうがもっともこうかてきとされている。",
             "This method is considered the most effective.", "best practice"),
        ],
    },
    {
        "slug": "どころか",
        "jlpt": "n3",
        "module": "03-n3",
        "deck": "03 - N3",
        "rows": [
            ("彼は謝るどころか、文句を言った。", "どころか",
             "かれはあやまるどころか、もんくをいった。",
             "Far from apologising, he complained.", "expected vs actual"),
            ("寒いどころか、雪まで降っている。", "どころか",
             "さむいどころか、ゆきまでふっている。",
             "Not only cold — it's even snowing.", "intensification"),
            ("お礼を言われるどころか、無視された。", "どころか",
             "おれいをいわれるどころか、むしされた。",
             "Far from being thanked, I was ignored.", "expected vs actual"),
            ("痩せるどころか、太ってしまった。", "どころか",
             "やせるどころか、ふとってしまった。",
             "Far from losing weight, I gained.", "goal vs outcome"),
            ("楽しむどころか、苦痛だった。", "どころか",
             "たのしむどころか、くつうだった。",
             "Far from enjoying it, it was painful.", "expectation reversed"),
        ],
    },
    {
        "slug": "とは",
        "jlpt": "n1",
        "module": "05-n1",
        "deck": "05 - N1",
        "rows": [
            ("まさか彼が来るとは思わなかった。", "とは",
             "まさかかれがくるとはおもわなかった。",
             "I never expected him to come.", "expressing surprise"),
            ("自由とは何か。", "とは",
             "じゆうとはなにか。",
             "What is 'freedom'?", "rhetorical definition"),
            ("これほど大変だとは知らなかった。", "とは",
             "これほどたいへんだとはしらなかった。",
             "I didn't know it would be this hard.", "underestimated difficulty"),
            ("友達に裏切られるとは、悲しい。", "とは",
             "ともだちにうらぎられるとは、かなしい。",
             "To be betrayed by a friend — how sad.", "lamenting situation"),
            ("彼女が結婚するとは驚きだ。", "とは",
             "かのじょがけっこんするとはおどろきだ。",
             "It's a surprise that she's getting married.", "surprise at news"),
        ],
    },
    {
        "slug": "や否や",
        "jlpt": "n1",
        "module": "05-n1",
        "deck": "05 - N1",
        "rows": [
            ("彼が部屋に入るや否や、皆が立ち上がった。", "や否や",
             "かれがへやにはいるやいなや、みながたちあがった。",
             "The moment he entered the room, everyone stood up.", "immediate reaction"),
            ("ベルが鳴るや否や、子供たちは外へ走り出した。", "や否や",
             "べるがなるやいなや、こどもたちはそとへはしりだした。",
             "The moment the bell rang, the children ran outside.", "school bell"),
            ("電話を切るや否や、また鳴った。", "や否や",
             "でんわをきるやいなや、またなった。",
             "The moment I hung up the phone, it rang again.", "rapid sequence"),
            ("ニュースを聞くや否や、彼女は泣き出した。", "や否や",
             "にゅーすをきくやいなや、かのじょはなきだした。",
             "The moment she heard the news, she burst into tears.", "emotional reaction"),
            ("雨が降り始めるや否や、傘を開いた。", "や否や",
             "あめがふりはじめるやいなや、かさをひらいた。",
             "The moment it started raining, I opened my umbrella.", "instant response"),
        ],
    },
    {
        "slug": "いたす",
        "jlpt": "n4",
        "module": "02-n4",
        "deck": "02 - N4",
        "rows": [
            ("私が説明いたします。", "いたします",
             "わたしがせつめいいたします。",
             "I will explain (humble).", "humble offer to explain"),
            ("後ほどご連絡いたします。", "いたします",
             "のちほどごれんらくいたします。",
             "I will contact you later (humble).", "humble follow-up"),
            ("ご案内いたします。", "いたします",
             "ごあんないいたします。",
             "I will show you the way (humble).", "humble guiding"),
            ("失礼いたします。", "いたします",
             "しつれいいたします。",
             "Excuse me (humble; entering/leaving).", "humble entry / departure"),
            ("お手伝いいたします。", "いたします",
             "おてつだいいたします。",
             "I will assist you (humble).", "humble offer to help"),
        ],
    },
]


def make_dictation(entry):
    deck = f"Japanese Grammar::{entry['deck']} Grammar::Dictation"
    header = (
        "#separator:tab\n"
        "#html:true\n"
        "#columns:Audio\tPrompt\tAnswer\tReading\tEN\tTags\n"
        "#notetype:Dictation\n"
        f"#deck:{deck}\n"
        "\n"
    )
    body = []
    for transcript, target, reading, en, _hint in entry["rows"]:
        # Prompt = sentence with target replaced by ___ (first occurrence only)
        prompt = transcript.replace(target, "___", 1)
        tags = (
            f"module:{entry['module']} "
            f"jlpt:{entry['jlpt']} "
            f"point:{entry['slug']} "
            f"complexity:standard "
            f"source:authored "
            f"frequency:top10k "
            f"scaffold:pending-audio"
        )
        body.append(f"[sound:pending.mp3]\t{prompt}\t{target}\t{reading}\t{en}\t{tags}\n")
    return header + "".join(body)


def make_listening(entry):
    deck = f"Japanese Grammar::{entry['deck']} Grammar::Listening"
    header = (
        "#separator:tab\n"
        "#html:true\n"
        "#columns:Audio\tTranscript\tReading\tEN\tHint\tTags\n"
        "#notetype:Listening\n"
        f"#deck:{deck}\n"
        "\n"
    )
    body = []
    for transcript, _target, reading, en, hint in entry["rows"]:
        tags = (
            f"module:{entry['module']} "
            f"jlpt:{entry['jlpt']} "
            f"point:{entry['slug']} "
            f"complexity:standard "
            f"source:authored "
            f"frequency:top10k "
            f"scaffold:pending-audio"
        )
        body.append(f"[sound:pending.mp3]\t{transcript}\t{reading}\t{en}\t{hint}\t{tags}\n")
    return header + "".join(body)


def main():
    for entry in PAIRS:
        dpath = Path(f"grammar-strict/{entry['module']}/{entry['slug']}_dictation.tsv")
        lpath = Path(f"grammar-strict/{entry['module']}/{entry['slug']}_listening.tsv")
        dpath.write_text(make_dictation(entry), encoding="utf-8")
        lpath.write_text(make_listening(entry), encoding="utf-8")
        print(f"  WROTE {dpath.name} + {lpath.name}  ({len(entry['rows'])} rows each)")
    print(f"\nTotal: {2 * len(PAIRS)} files re-authored.")


if __name__ == "__main__":
    main()
