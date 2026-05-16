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

For every grammar point we generate up to **six** card types (extended from
the English Verb System deck's four-card matrix to handle Japanese-specific
challenges — listening discrimination + dictation):

| Note type | Front shows | Back shows | Purpose |
|---|---|---|---|
| **Recognition** | Japanese sentence | label · formula · main use · quick cue · contrast · pitch · 🔊 | "I see this in the wild — what is it?" |
| **Production** | English prompt + target form | model JP sentence + reading + why + 🔊 (alt-voice optional) | "I need to say X — how?" |
| **Cloze** | sentence with `{{c1::…}}` blank | full sentence + reading + hint + 🔊 | Fill-in-the-blank, builds collocation memory |
| **Contrast** | sentence + two options | answer + why + tip + 🔊 | A/B minimal-pair drill (は vs が, に vs で, etc.) |
| **Listening** | 🔊 only | transcript + furigana + meaning | Discriminate near-homophones (-ている vs -てる, -てある vs -ている) |
| **Dictation** | 🔊 sentence | fill the blank in the displayed frame + full reading | Particle ellipsis recovery, aspect awareness |

A grammar point typically yields **3–10 cards** across these note types
depending on difficulty, polysemy and contrastiveness. Polysemous points
(e.g. -ている has progressive / habitual / resultative readings) get one
card per sense plus pairwise contrast cards.

Every card carries machine-generated furigana (hiragana over kanji), a
Hepburn romaji line on the back, an NHK-style pitch-accent overlay
(when the token is in `media/pitchaccent_index.json`), and at least one
Google-Cloud-TTS Japanese audio clip of the JP sentence (primary voice
plus an optional `_alt.mp3` second-voice variant for variety).

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

### Wave 1 — Foundation (Module 00) — **~470 cards**
1. **Kana** — 46 base + 25 dakuten/handakuten + 33 yō-on combos = **104 cards**
2. **Pitch-accent primer** — full intro + Tokyo pattern table + **80 cards**
   covering all four classes (heiban / atamadaka / nakadaka / odaka),
   compound shifts, and verb-stem accent shifts on -ます / -て / -た.
   Each card overlays the L/H contour above the kana — fed by
   `media/pitchaccent_index.json`.
3. **Verb-group fundamentals** — 30 cards: る/う dichotomy with diagnostic
   examples, irregular する・くる・行く, why -ます exists (auxiliarised
   2類 history), stem isolation rules, vowel-harmony in -て / -た.
4. **Particles core** (は・が・を・に・で・へ・と・も・から・まで) —
   40 recognition + **40 contrast** cards. Contrast set is *exhaustive*
   on the high-confusion sub-matrix:
   * は vs が — 8 minimal pairs (topic vs exhaustive listing,
     existentials, negation, embedded clauses, emphasis)
   * に vs で — 6 pairs (location-of-existence vs location-of-event,
     instrument vs purpose, time-point vs time-span)
   * へ vs に — 4 pairs (direction vs goal)
   * から vs より — 3 pairs (origin vs comparison)
   * や vs と vs とか — 3 pairs (exhaustive vs partial vs colloquial)
   * ばかり vs だけ vs しか — 4 pairs (volume vs limit vs exclusion)
5. **Copula** です/だ + negative/past/te-form/conditional — 40 cards
   (4 declension cells × 4 polarity-tense combinations + classical
    なり / たり ancestry + でございます polite extension).
6. **Numbers + 8 most-used counters** (つ・人・本・枚・匹・台・冊・回) —
   100 cards including rendaku/sokuon irregularities (一本 vs 三本,
   一匹 vs 三匹, 一回 vs 八回).
7. **Time expressions** — 25 cards (今日 / 明日 / 昨日 / 〜時 / 〜分 /
   午前 / 午後 / 来週 / 先月 / 半 endings).
8. **Demonstratives** (これ系・それ系・あれ系・どれ系 + 連体 vs 名詞 forms)
   — 25 cards.

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

### Wave 3 — N4 Grammar (Module 02) — **~720 cards**

The ~150 N4 points, expanded into the following high-confusion sub-clusters
(each treated as a coherent unit so the contrast cards form a coherent
matrix, not isolated drills):

* **Voice & valency** — passive (-れる/-られる), causative (-せる/-させる),
  causative-passive (-せられる/-させられる), suffering passive
  (迷惑の受身), honorific passive (お読みになる) — full grid of 30 contrast
  cards covering "real" vs adversative passive and the 自他動詞 distinction.
* **Conditional family** (と・ば・たら・なら) — full 16-cell matrix:
  4 conditionals × 4 use-patterns (general truth, hypothetical, sequential,
  presupposition). Plus もし / 仮に / 万一 hypothetical adverbs and the
  pragmatic difference between -ば-good-result and -たら-narrative-shift.
  ~50 cards.
* **Aspectual cluster** — explicitly disambiguates the **3 readings of
  -ている** (ongoing / habitual / resultative) with one card per sense and
  pairwise contrast cards, plus the full -て-aux family:
  -ている / -てある / -ておく / -てしまう / -てみる / -ていく / -てくる /
  -てある-vs-ている-resultative. ~60 cards.
* **Giving / receiving** — あげる / さしあげる / やる, もらう / いただく,
  くれる / くださる, plus benefactive -てあげる / -てもらう / -てくれる
  with directionality + in-group/out-group rules. ~50 cards.
* **Evidential cluster** — -そう (hearsay) vs -そう (appearance), -ようだ
  (visual inference) vs -らしい (report) vs -みたいだ (informal simile)
  vs -っぽい (slight tendency), with negation forms (-そうもない,
  -らしくない). 30 contrast cards.
* **Transitive ↔ intransitive verb pairs** — top 40 pairs (開く/開ける,
  落ちる/落とす, 始まる/始める, 入る/入れる, 出る/出す, 集まる/集める,
  伝わる/伝える, 育つ/育てる, …), 4 cards per pair (recognition,
  production, cloze, contrast). ~160 cards.
* **Volitional + potential** — -よう / -ましょう / -(ら)れる potential
  + できる, with negation and embedded-clause uses. ~30 cards.
* **〜ところ aspectual** — 〜ところだ (about to) / 〜ているところ (in the
  middle of) / 〜たところ (just finished). 12 cards.
* **〜たことがある** experiential vs **〜ことがある** habitual. 8 cards.
* **Other N4 points** — 〜なければならない and contractions (-なきゃ),
  〜てもいい / 〜てはいけない / 〜なくてもいい permission-prohibition
  triangle, 〜たほうがいい advice, 〜つもり intent vs 〜予定 schedule,
  〜ようとする attempted action, etc. ~140 cards.

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

### Wave 7 — Keigo (Module 06) — **~400 cards**
* **Sonkeigo (尊敬語) verb table** — ~30 irregular replacement pairs
  (いらっしゃる ← いる/くる/いく, 召し上がる ← 食べる/飲む, ご覧になる ←
  見る, おっしゃる ← 言う, なさる ← する, …). Recognition + production
  for each.
* **Kenjōgo (謙譲語) verb table** — ~20 irregular replacement pairs
  (伺う, 申す, いたす, 拝見する, 存じる, 参る, 差し上げる, …).
* **Teineigo (丁寧語)** — です/ます polite layer, ございます, でございます,
  -まして / -まする legacy forms, polite-in-subordinate-clause pattern.
* **Bikago (美化語)** — お/ご prefix patterns + lexical restrictions
  (お酒/お茶/お米 ✓, *おビール ✗ — exceptions matter).
* **Productive constructions**:
  * お/ご + masu-stem + になる (sonkeigo)
  * お/ご + masu-stem + する/いたす (kenjōgo)
  * -(さ)せていただく (humble request, modern over-use cautioned)
  * Honorific passive (お読みになる ↔ 読まれる) + their stacking interaction
  * Honorific negation (いらっしゃらない / おっしゃらない)
* **Customer-service / business set phrases** (~40 cards):
  少々お待ちください / 恐れ入りますが / 申し訳ございません /
  かしこまりました / お手数をおかけしますが / 失礼いたします etc.
* **Register-shift contrast cards** — 〜30 minimal pairs at different
  politeness rungs (行く / いらっしゃる / 参る) for the same referent.

### Wave 8 — Casual / Spoken (Module 07) — **~300 cards**
* **Aspectual contractions** — 〜てる ← 〜ている, 〜てく ← 〜ていく,
  〜とく ← 〜ておく, 〜てる/とる Kansai variants, 〜ちゃう/〜じゃう ← 〜てしまう.
* **Obligation contractions** — 〜なきゃ ← 〜なければ, 〜なくちゃ ← 〜なくては,
  〜なきゃならん, 〜なきゃ! as standalone implicit obligation.
* **Pragmatic contractions** — 〜たら？ as suggestion, 〜って quotative
  (3 distinct uses), んで ← ので, だろ?/でしょ?, じゃない/じゃん,
  sentence-trailing 〜し as soft because-list.
* **Particle ellipsis** — explicit drill set on which particles get
  dropped in casual speech and which can't:
  * を → reliably dropped (それ食べる, この本読む)
  * は → dropped in answers (好き好き / うん、行く)
  * に → dropped in time/destination (明日行く, 駅着いた)
  * が → dropped only in topic-fronted statements
  * で → almost never dropped (instrumental keeps)
  ~25 cloze + contrast cards with audio (you must HEAR the gap).
* **Sentence-final softeners** in casual register — のだ → んだ → の?,
  でしょ → だろ → でしょ?, よね → よな (male).

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

### Wave 14 — Negation paradigm (cross-module)
Japanese negation is morphologically dense and learner-confusable. This
wave produces a dedicated cross-module sub-deck (~120 cards) that gathers
every negative form into a single paradigm:

* Verb negation: -ない / -ぬ / -ず / -ません — register gradient
* Negative te-form: -なくて vs -ずに vs -ないで (semantic differences)
* Adjective negation: い-adj 〜くない vs な-adj 〜じゃない/ではない
* Aspectual negation: -ていない (ongoing-not) vs -ない (event-not)
* Honorific negation: いらっしゃらない vs おっしゃらない vs お読みにならない
* Idiomatic double-negatives: 〜ないことはない, 〜ずにはいられない,
  〜ないわけではない, 〜ぬことはない (literary)
* Negation in conditionals: 〜なければ vs 〜ないと vs 〜なかったら

### Wave 15 — Sentence-mining template (Module 14, opt-in)
Blank Recognition / Production / Cloze TSV templates under
`grammar/14-mining/`, plus tagging guide so learners can add their own
sentences from immersion (anime, manga, podcasts, news) and have them
flow through the same audio + furigana + pitch-accent pipeline as the
shipped corpus. Includes:
* `template_recognition.tsv` / `template_production.tsv` / `template_cloze.tsv`
  with explanatory `#` comments
* `MINING_GUIDE.md` covering: how to extract sentences with Yomitan,
  how to fill the columns, how to re-run the pipeline, how to tag
  with `source:anime-…`, `source:nhk-…` for later filtering.

### Wave 16 — L1 Interference (Module 13)
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
| `register:*` | `formal`, `polite`, `neutral`, `casual`, `slang`, `vulgar`, `literary`, `keigo-sonkei`, `keigo-kenjo`, `keigo-teinei`, `feminine-casual`, `masculine-casual` |
| `frequency:*` | `top1k`, `top5k`, `top10k`, `low` (BCCWJ-derived) |
| `domain:*` | `everyday`, `business`, `academic`, `news`, `anime-manga`, `gaming`, `internet`, `dialect-kansai`, `dialect-tohoku`, `…` |
| `jlpt:*` | `n5`, `n4`, `n3`, `n2`, `n1`, `beyond` |
| `module:*` | `00-foundation` … `14-mining` |
| `point:*` | grammar-point slug, e.g. `te-iru-progressive`, `wake-da` |
| `pos:*` | `verb`, `adj-i`, `adj-na`, `adverb`, `particle`, `aux`, `expr` |
| `sense:*` | for polysemous points: `te-iru-progressive`, `te-iru-resultative`, `te-iru-habitual`, … (one card per sense) |
| `confusable-with:*` | comma-list of point slugs that share a contrast card |
| `ambiguity:*` | `unambiguous`, `context-dependent`, `highly-polysemous` |
| `complexity:*` | `1`–`5` (mora + clause-depth heuristic, fed by validator) |
| `source:*` | `shin-kanzen`, `tofugu`, `imabi`, `bunpro`, `dictionary-of-jp-grammar`, or for user-mined sentences: `anime-…`, `nhk-…`, `twitter-…` |

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
