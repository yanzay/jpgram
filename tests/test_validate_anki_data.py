#!/usr/bin/env python3
"""Regression tests for release-blocking TSV validation."""
from __future__ import annotations

from collections import defaultdict

import validate_anki_data as validator


def _hash_audio(text: str) -> str:
    return f"{validator._audio_hash(text)}.mp3"


def test_audio_ref_must_match_current_source_sentence(tmp_path, monkeypatch):
    monkeypatch.setattr(validator, "MEDIA_DIR", tmp_path)

    stale_ref = _hash_audio("犬がいます。")
    (tmp_path / stale_ref).write_bytes(b"ID3\x04\x00\x00\x00\x00\x00\x00")

    tsv = tmp_path / "sample_recognition.tsv"
    tsv.write_text(
        "\n".join(
            [
                "#separator:tab",
                "#html:true",
                "#columns:JP\tReading\tEN\tLabel\tFormula\tMainUse\tQuickCue\tContrast\tAudio\tTags",
                "#notetype:Recognition",
                (
                    "猫がいます。\tねこがいます。\tThere is a cat.\t"
                    "sample\tNoun + がいます\tpresence\tpresence\tvs あります\t"
                    f"[sound:{stale_ref}]\t"
                    "module:01-n5 jlpt:n5 point:sample source:test frequency:top1k complexity:intro"
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    errors = validator.lint_file(
        tsv,
        audio_users=defaultdict(list),
        manifest_keys={stale_ref[:-4]},
        taxonomy_points=set(),
    )

    assert any("does not match current source sentence" in err for err in errors)


def test_contrast_omit_audio_hash_uses_spoken_sentence():
    header = ["JP", "OptionA", "OptionB", "Answer", "Why", "Tip", "Audio", "Tags"]
    row = [
        "(初対面で)___田中です。",
        "私は",
        "(omit)",
        "(omit)",
        "Drop the pronoun in a self-introduction.",
        "self-introduction",
        "",
        "module:13-l1 point:l1-pronoun-overuse",
    ]

    assert validator._source_sentence("Contrast", header, row) == "田中です。"


def test_production_prompt_must_not_expose_japanese_form_hint(tmp_path, monkeypatch):
    monkeypatch.setattr(validator, "MEDIA_DIR", tmp_path)

    tsv = tmp_path / "sample_production.tsv"
    tsv.write_text(
        "\n".join(
            [
                "#separator:tab",
                "#html:true",
                "#columns:Prompt\tTarget\tReading\tSample\tWhy\tAudio\tTags",
                "#notetype:Production",
                (
                    "Say (it is worth doing) using からこそ.\tからこそ\t"
                    "むずかしいからこそ、やりがいがある。\t難しいからこそ、やりがいがある。\t"
                    "からこそ marks the precise reason.\t\t"
                    "module:03-n3 jlpt:n3 point:sample source:test frequency:top1k complexity:intro"
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    errors = validator.lint_file(
        tsv,
        audio_users=defaultdict(list),
        manifest_keys=set(),
        taxonomy_points=set(),
    )

    assert any("Production Prompt exposes a Japanese form hint" in err for err in errors)


def test_recognition_en_must_be_translation_not_production_prompt(tmp_path, monkeypatch):
    monkeypatch.setattr(validator, "MEDIA_DIR", tmp_path)

    tsv = tmp_path / "sample_recognition.tsv"
    tsv.write_text(
        "\n".join(
            [
                "#separator:tab",
                "#html:true",
                "#columns:JP\tReading\tEN\tLabel\tFormula\tMainUse\tQuickCue\tContrast\tAudio\tTags",
                "#notetype:Recognition",
                (
                    "今日は昨日より寒い。\tきょうはきのうよりさむい。\t"
                    "Say today is colder than yesterday.\tcomparison\tA は B より Adj\t"
                    "comparison baseline\tbaseline\tのほう\t\t"
                    "module:02-n4 jlpt:n4 point:sample source:test frequency:top1k complexity:intro"
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    errors = validator.lint_file(
        tsv,
        audio_users=defaultdict(list),
        manifest_keys=set(),
        taxonomy_points=set(),
    )

    assert any("production-style prompt leaked into Recognition EN" in err for err in errors)


def test_recognition_quickcue_must_not_duplicate_mainuse(tmp_path, monkeypatch):
    monkeypatch.setattr(validator, "MEDIA_DIR", tmp_path)

    tsv = tmp_path / "sample_recognition.tsv"
    tsv.write_text(
        "\n".join(
            [
                "#separator:tab",
                "#html:true",
                "#columns:JP\tReading\tEN\tLabel\tFormula\tMainUse\tQuickCue\tContrast\tAudio\tTags",
                "#notetype:Recognition",
                (
                    "彼は先生になりました。\tかれはせんせいになりました。\t"
                    "He became a teacher.\tbecome\tNoun + になる\t"
                    "change of status\tchange of status\tい-adj uses くなる\t\t"
                    "module:01-n5 jlpt:n5 point:sample source:test frequency:top1k complexity:intro"
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    errors = validator.lint_file(
        tsv,
        audio_users=defaultdict(list),
        manifest_keys=set(),
        taxonomy_points=set(),
    )

    assert any("Recognition QuickCue duplicates MainUse/Formula" in err for err in errors)
