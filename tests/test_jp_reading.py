#!/usr/bin/env python3
"""
Regression tests for scripts/jp_reading.py.

Run:  python -m pytest tests/test_jp_reading.py -v
  or: python tests/test_jp_reading.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from jp_reading import _num2kana, _minutes_reading, _age_reading, bad_reading_issues, reading


# ── Unit tests: number converter ─────────────────────────────────────────────

def test_num2kana_basics():
    assert _num2kana(1) == "いち"
    assert _num2kana(10) == "じゅう"
    assert _num2kana(11) == "じゅういち"
    assert _num2kana(100) == "ひゃく"
    assert _num2kana(300) == "さんびゃく"
    assert _num2kana(600) == "ろっぴゃく"
    assert _num2kana(800) == "はっぴゃく"
    assert _num2kana(1000) == "せん"
    assert _num2kana(3000) == "さんぜん"
    assert _num2kana(8000) == "はっせん"
    assert _num2kana(10000) == "いちまん"
    assert _num2kana(18) == "じゅうはち"


def test_minutes_reading():
    assert _minutes_reading(1) == "いっぷん"
    assert _minutes_reading(2) == "にふん"
    assert _minutes_reading(3) == "さんぷん"
    assert _minutes_reading(4) == "よんぷん"
    assert _minutes_reading(5) == "ごふん"
    assert _minutes_reading(6) == "ろっぷん"
    assert _minutes_reading(7) == "ななふん"
    assert _minutes_reading(8) == "はっぷん"
    assert _minutes_reading(9) == "きゅうふん"
    assert _minutes_reading(10) == "じゅっぷん"
    assert _minutes_reading(30) == "さんじゅっぷん"
    assert _minutes_reading(16) == "じゅうろっぷん"


def test_age_reading():
    assert _age_reading(1) == "いっさい"
    assert _age_reading(8) == "はっさい"
    assert _age_reading(18) == "じゅうはっさい"
    assert _age_reading(20) == "はたち"
    assert _age_reading(25) == "にじゅうごさい"


# ── Unit tests: bad_reading_issues ───────────────────────────────────────────

def test_bad_reading_issues_clean():
    assert bad_reading_issues("みずをひゃくどにあたためると、ふきます。") == []
    assert bad_reading_issues("さむいかぜがはいってきた。") == []


def test_bad_reading_issues_kanji():
    issues = bad_reading_issues("水を100℃に熱すると沸きます。")
    assert any("kanji" in i for i in issues)


def test_bad_reading_issues_digits():
    issues = bad_reading_issues("みずを100どに")
    assert any("digit" in i for i in issues)


def test_bad_reading_issues_symbol():
    issues = bad_reading_issues("みずをひゃく℃に")
    assert any("℃" in i or "symbol" in i for i in issues)


def test_bad_reading_issues_sokuon_double():
    issues = bad_reading_issues("さむいかぜがいっってきた。")
    assert any("sokuon" in i for i in issues)

    issues2 = bad_reading_issues("ーーびょうき")
    assert any("sokuon" in i for i in issues2)


# ── Integration tests: reading() ─────────────────────────────────────────────

def test_numeral_temperature():
    r = reading("水を100℃に熱すると、沸きます。")
    assert "100" not in r
    assert "℃" not in r
    assert "ひゃくど" in r


def test_numeral_minutes():
    r = reading("30分後に来てください。")
    assert "30" not in r
    assert "さんじゅっぷん" in r


def test_numeral_age():
    r = reading("彼女は18歳です。")
    assert "18" not in r
    assert "じゅうはっさい" in r


def test_kanji_clock_seven():
    r = reading("七時に起きます。")
    assert "しちじ" in r
    assert "ななじ" not in r


def test_kanji_clock_nine():
    r = reading("九時に寝ます。")
    assert "くじ" in r


def test_pronoun_kare():
    r = reading("彼が来た。")
    assert "かれ" in r
    assert "かの" not in r


def test_pronoun_kanojo():
    r = reading("彼女が来た。")
    assert "かのじょ" in r


def test_okane():
    r = reading("お金がない。")
    assert "おかね" in r
    assert "おきん" not in r


def test_iu_not_yuu():
    r = reading("彼はそう言う。")
    assert "いう" in r
    assert "ゆう" not in r


def test_ya_ina_ya():
    r = reading("帰るや否や寝た。")
    assert "やいなや" in r


def test_gaikokujin():
    r = reading("外国人が多い。")
    assert "がいこくじん" in r
    assert "がいこくにん" not in r


def test_akeru_transitive_full_sentence():
    r = reading("ドアを開けると、寒い風が入ってきた。")
    assert r == "どあをあけると、さむいかぜがはいってきた。"


# ── Regression tests added 2026-05-22 (Phase 1) ─────────────────────────────


def test_hikari_to_kage():
    r = reading("光と影が織りなす場面。")
    assert "ひかりとかげ" in r
    assert "ひかとかげ" not in r


def test_wakaki_hi():
    r = reading("若き日にして既に才能を示した。")
    assert "わかきひ" in r
    assert "わかきにち" not in r


def test_kenkou():
    r = reading("私の健康が大切だ。")
    assert "けんこう" in r
    # UniDic should never give きれい for 健康
    assert "きれい" not in r


def test_yomigaeru():
    r = reading("会えて蘇った気持ちだ。")
    assert "よみがえった" in r
    assert "よみがった" not in r


def test_mitame():
    r = reading("見た目が大事。")
    assert "みため" in r
    assert "みたため" not in r


def test_okonau_with_wo():
    r = reading("会議を行う。")
    assert "おこなう" in r


def test_okonau_with_wo_te_form():
    r = reading("研究を行った。")
    assert "おこなった" in r


def test_iku_with_ni():
    """行く (motion verb) — make sure okonau override doesn't break 行く."""
    r = reading("駅に行きました。")
    assert "いきました" in r
    assert "おこな" not in r


def test_ageru_listening_in_group_safe():
    """The あげる listening file was fixed; new sentence reads correctly."""
    r = reading("私は新人の同僚に仕事を教えてあげた。")
    assert "わたしはしんじん" in r
    assert "おしえてあげた" in r


def test_imminent_imperative_nasai():
    r = reading("早く起きなさい。")
    assert "はやくおきなさい" in r


def test_polite_suggestion_mashou():
    r = reading("一緒に映画を見ましょう。")
    assert "いっしょにえいがをみましょう" in r


def test_doko_kara():
    r = reading("どこから来ましたか？")
    assert "どこからきましたか" in r


def test_pitch_primer_atarashii_kotoba():
    """Pitch primer fixes: ensure new readings are correct."""
    assert reading("遊ぶ") == "あそぶ"
    assert reading("橋") == "はし"
    assert reading("点") == "てん"
    assert reading("弟") == "おとうと"


if __name__ == "__main__":
    import traceback
    failed = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  PASS  {name}")
            except Exception as e:
                print(f"  FAIL  {name}: {e}")
                traceback.print_exc()
                failed += 1
    print(f"\n{'All tests passed' if not failed else f'{failed} test(s) failed'}.")
    sys.exit(failed)
