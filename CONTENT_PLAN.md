# Japanese Grammar Anki — Content Plan

> Goal: a single Anki package that comprehensively covers **every** Japanese
> grammar point a learner will meet from absolute zero up to and beyond JLPT N1,
> plus the everyday speech, slang, keigo, sentence-final particles, and
> idiomatic constructions that no JLPT prep book actually teaches.
>
> This file is the **content backbone**. Each section lists every grammar point
> we plan to ship, grouped into modules that map 1:1 onto sub-decks in the
> final `.apkg`. Generation happens in waves; each wave produces one or more
> TSVs under `grammar/<module>/` and is checked in before we move to the next.

---

## Card-type matrix

For every grammar point we generate **four** card types (the same matrix as
the English Verb System deck — proven pedagogy):

| Note type | Front shows | Back shows | Purpose |
|---|---|---|---|
| **Recognition** | Japanese sentence | label · formula · main use · quick cue · contrast · 🔊 | "I see this in the wild — what is it?" |
| **Production** | English prompt + target form | model JP sentence + reading + why + 🔊 | "I need to say X — how?" |
| **Cloze** | sentence with `{{c1::…}}` blank | full sentence + reading + hint + 🔊 | Fill-in-the-blank, builds collocation memory |
| **Contrast** | sentence + two options | answer + why + tip + 🔊 | A/B minimal-pair drill (e.g. は vs が) |

A grammar point typically yields **3–8 cards** across these four note types
depending on its difficulty and contrastiveness.

Every card carries machine-generated furigana (hiragana over kanji) and a
Hepburn romaji line on the back, plus a Google-Cloud-TTS Japanese audio clip
of the JP sentence.

---

## Deck hierarchy

```
Japanese Grammar
├── 00 - Foundation                         ← always-on
│   ├── Hiragana & Katakana                 (kana mnemonics, voicing, yō-on)
│   ├── Pitch-accent primer                 (heiban / atamadaka / nakadaka / odaka)
│   ├── Particles core                      (は が を に で へ と も から まで)
│   ├── Copula & です/だ                    (polite vs plain)
│   ├── Numbers & counters                  (つ・人・本・枚・匹・台 …)
│   └── Time expressions                    (今日・明日・〜時・〜分)
│
├── 01 - N5 Grammar                         (~140 points)
├── 02 - N4 Grammar                         (~150 points)
├── 03 - N3 Grammar                         (~190 points)
├── 04 - N2 Grammar                         (~220 points)
├── 05 - N1 Grammar                         (~260 points)
│
├── 06 - Keigo / Honorifics                 (sonkeigo, kenjōgo, teineigo, bikago)
├── 07 - Casual / Spoken Forms              (-てる / -ちゃう / -じゃん …)
├── 08 - Slang & Internet Speech            (ガチ・草・りょ・ぴえん・KY)
├── 09 - Sentence-Final Particles & Aizuchi (よ ね な わ かしら ぞ ぜ さ + 相槌)
├── 10 - Onomatopoeia                       (擬音語 + 擬態語, 300+ items)
├── 11 - Classical / Literary Carryover     (べし・ず・なり・けり in modern texts)
├── 12 - Beyond N1                          (idioms, set phrases, 四字熟語, ことわざ)
└── 13 - L1 Interference                    (per-language contrast drills)
```

Estimated final size: **~6,500 unique cards across ~4,000 grammar points.**

---

## Generation waves

Each wave is a self-contained PR with TSVs + audio + tag injection.
After every wave: `validate_anki_data.py && build_audio.py --dry-run`.

### Wave 0 — Skeleton (this commit)
* Project scaffolding, audio pipeline, content plan, empty `grammar/` tree.

### Wave 1 — Foundation (Module 00)
1. Kana — 46 base + 25 dakuten/handakuten + 33 yō-on combos = **104 cards**
2. Pitch-accent primer — 20 minimal-pair examples
3. Particles core (は・が・を・に・で・へ・と・も・から・まで) — 40 recognition + 30 contrast cards
4. Copula です/だ + negative/past/te-form — 24 cards
5. Numbers + 8 most-used counters — 60 cards
6. Time expressions — 25 cards

### Wave 2 — N5 Grammar (Module 01)
The 140 points in the N5 syllabus, in pedagogical order:

```
verbs:        る/う dichotomy, polite -ます, neg -ません, past -ました,
              te-form rules, -ている (progressive), -てください,
              -たい (desire), -ながら, -ましょう
adjectives:   い-adj vs な-adj, conjugation full grid, attributive vs predicative
particles:    extended set (より・しか・だけ・ばかり in early use)
constructions:〜があります/います, 〜が好きです, 〜が分かります,
              〜と思います, 〜と言います, 〜つもりです,
              〜ことができる, 〜なければなりません, 〜てもいい,
              〜てはいけない, 〜なくてもいい, 〜たことがある,
              〜たほうがいい
question/Q:   〜か, 〜ね, 〜よ, なに/なん/だれ/どこ/いつ/どう/いくら/いくつ
demonstrate:  これ/それ/あれ/どれ + this/that/which family
```

### Wave 3 — N4 Grammar (Module 02)
The 150 N4 points: passive, causative, causative-passive, conditional families
(と・ば・たら・なら), volitional, potential, transitive↔intransitive verb pairs,
giving/receiving (あげる・もらう・くれる + benefactive forms), 〜そう/〜よう/
〜らしい/〜みたい (evidential cluster), 〜ところ aspectual cluster, etc.

### Wave 4 — N3 Grammar (Module 03)
~190 points: 〜わけ family (わけだ・わけではない・わけがない・わけにはいかない),
〜ばかり family, 〜ところ family, 〜うえ・〜うちに・〜さえ・〜こそ・〜ほど,
embedded questions, complex causatives, advanced conditional shading, etc.

### Wave 5 — N2 Grammar (Module 04)
~220 points: 〜にあたって・〜に応じて・〜に基づいて・〜にかかわらず・
〜にかぎって, 〜どころか, 〜つつ, 〜まま, 〜ながらも, 〜限り, 〜次第,
〜ものの, 〜ものか, 〜ことだ・〜ものだ・〜ことか etc.

### Wave 6 — N1 Grammar (Module 05)
~260 points: 〜ずにはいられない, 〜てやまない, 〜にかたくない, 〜とあって,
〜ゆえに, 〜きらいがある, 〜いかんによらず, 〜まじき, 〜ながらも /
〜ながらに, full classical-derived endings still alive in modern formal
Japanese (〜べき・〜ぬ・〜ざる).

### Wave 7 — Keigo (Module 06)
* Sonkeigo (尊敬語) verb table — irregular replacements (いらっしゃる, 召し上がる, ご覧になる, …)
* Kenjōgo (謙譲語) verb table — irregular replacements (伺う, 申す, いたす, 拝見する, …)
* Teineigo (丁寧語) — です/ます polite layer, ございます, でございます
* Bikago (美化語) — お and ご prefix patterns, lexical restrictions
* O-+stem-ni-naru / o-+stem-suru construction patterns
* Customer-service set phrases (「少々お待ちください」etc.)

### Wave 8 — Casual / Spoken (Module 07)
〜てる ← 〜ている, 〜てく ← 〜ていく, 〜てる/とる Kansai variants,
〜なきゃ/〜なくちゃ/〜なきゃならん contractions, 〜ちゃう/〜じゃう,
〜たら？ as suggestion, 〜って quotative, んで (because), だろ?/でしょ?,
じゃない/じゃん, dropping particles in speech, sentence-trailing 〜し.

### Wave 9 — Slang & Internet (Module 08)
**Top-popular** modern slang only — explicitly marked register-NSFW where
relevant. Examples: ガチ, マジ, やばい (positive/negative), ウケる, 草 / w / ww,
KY, りょ / りょうかい, ぴえん, ぴえん超えてぱおん, それな, 詰む / 詰んだ,
バズる, エモい, パリピ, ワンチャン, 推し / 推し活, リア充, 黒歴史, 中二病,
ググる, タピる, カミングアウト ➜ カミングアウトする, タイパ / コスパ.
Also: youth abbreviations (あけおめ・ことよろ・了解→りょ・おはよう→おは),
gaming/Twitter/TikTok loans, Generation Z vs Millennial vs Showa-era split.

### Wave 10 — Sentence-final particles & aizuchi (Module 09)
よ・ね・よね・な・なあ・かな・かしら・わ (female + Kansai male)・ぞ・ぜ・
さ・の・もの・ものか・じゃん・っけ — full pragmatic-force chart with
register and gender notes.
Aizuchi (相槌): はい・ええ・うん・そう・そうですね・そうなんですか・なるほど・
へえ・ほんと？・マジ？・やっぱり — when to use which.

### Wave 11 — Onomatopoeia (Module 10)
~300 high-frequency 擬音語 + 擬態語: ぺこぺこ・わくわく・どきどき・
ぴかぴか・ふわふわ・もちもち・さらさら・ざあざあ・ごろごろ・がらがら …
Each card pairs the onomatopoeia with its grammatical attachment pattern
(〜する・〜と・bare adverb).

### Wave 12 — Classical carryover (Module 11)
The pieces of 古文 / 文語 still alive in modern formal/literary Japanese:
〜べし / べき, 〜ず / 〜ぬ (negation), 〜ざる, 〜なり / 〜たり (assertion),
〜けり / 〜き (past), 〜む (volitional ancestor), 〜しめる (literary causative),
plus Sino-Japanese 漢文 reading order markers learners encounter in news.

### Wave 13 — Beyond N1 (Module 12)
* 四字熟語 (yojijukugo) — top 200 by frequency in modern prose
* ことわざ (proverbs) — top 150 with situational examples
* 慣用句 (idioms) — body-part + animal idioms (~250)
* Set business phrases (お疲れさまです, よろしくお願いします, 恐れ入りますが …)
* Discourse markers in formal writing (なお・ただし・しかしながら・もっとも・
  すなわち・いわゆる・むしろ)

### Wave 14 — L1 Interference (Module 13)
One sub-deck per L1, drilling the contrasts that THAT L1 trips on:
* 🇬🇧 English speakers — は vs が, transitive/intransitive pairs, particle drop, V-final word order
* 🇷🇺 Russian speakers — articles-N/A, aspect mapping (perfective/imperfective ↔ -た/-ている), motion verbs
* 🇨🇳 Chinese speakers — kanji false friends, tense (Chinese has none), particles (likewise), kanji compounds with different JP readings/meanings
* 🇰🇷 Korean speakers — surface-similar grammar but radically different keigo conventions, particle false friends (-が ≠ -이/가 in pragmatics)
* 🇪🇸 / 🇩🇪 / 🇫🇷 — TBD, opt-in only

Each L1 sub-deck binds to a separate Anki options preset that's set to
**0 new cards/day** by default — learners switch their L1 to the main preset
when they're ready (same opt-in pattern as the verbs deck).

---

## Tagging taxonomy

Every card is tagged along three orthogonal axes (auto-injected by
`scripts/apply_taxonomy_tags.py`, mirroring the verbs deck pattern):

| Axis | Values |
|---|---|
| `register:*` | `formal`, `polite`, `neutral`, `casual`, `slang`, `vulgar`, `literary`, `keigo-sonkei`, `keigo-kenjo`, `keigo-teinei` |
| `frequency:*` | `top1k`, `top5k`, `top10k`, `low` |
| `domain:*` | `everyday`, `business`, `academic`, `news`, `anime-manga`, `gaming`, `internet`, `dialect-kansai`, `dialect-tohoku`, `…` |
| `jlpt:*` | `n5`, `n4`, `n3`, `n2`, `n1`, `beyond` |
| `module:*` | `00-foundation` … `13-l1` |
| `point:*` | grammar-point slug, e.g. `te-form-progressive`, `wake-da` |
| `pos:*` | `verb`, `adj-i`, `adj-na`, `adverb`, `particle`, `aux`, `expr` |

---

## Pedagogy invariants

These rules govern every card we ship:

1. **One JP sentence ≤ 25 morae.** Longer sentences split into multiple cards.
2. **Every card has audio.** No exceptions. Audio is rendered by `build_audio.py`.
3. **Every card with kanji has furigana on the back.** Generated by `build_furigana.py`.
4. **Romaji never on the front.** Romaji only on the back, as a learning aid for the first ~3 months.
5. **Contrast cards must be minimal pairs.** Differ in ONE grammatical feature only.
6. **Production cards must be answerable.** Prompt + target form must uniquely determine an acceptable answer.
7. **No dictionary-form-only entries.** Every grammar point appears in at least one full sentence.
8. **Slang/vulgar cards are tagged `register:slang` or `register:vulgar`** and bound to the opt-in preset.
9. **No dead grammar.** A grammar point is included only if it's attested in modern (post-1990) corpora.

---

## Source authorities

When sources disagree, this is our priority order:

1. **The Dictionary of {Basic, Intermediate, Advanced} Japanese Grammar** (Makino & Tsutsui) — definitive on N5–N3.
2. **新完全マスター文法** (Shin Kanzen Master Grammar) N3 / N2 / N1 — the JLPT-aligned standard.
3. **A Reference Grammar of Japanese** (Martin) — historical / structural backstop.
4. **Imabi.org** + **Tofugu** — cross-checks for nuance in modern usage.
5. **NHK 日本語発音アクセント新辞典** — pitch accent.
6. For slang: **Tofugu**, **Nihongo so Matome**, native speaker spot-checks via curated Twitter/Reddit/Discord corpora; cross-reference 2 sources before inclusion.
