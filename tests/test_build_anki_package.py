#!/usr/bin/env python3
"""Regression tests for deck hierarchy and scheduling defaults."""
from __future__ import annotations

import build_anki_package as builder


def test_resolve_l1_deck_name_inserts_source_language(tmp_path):
    l1_dir = tmp_path / "13-l1"
    l1_dir.mkdir()
    tsv = l1_dir / "l1-pronoun-overuse_recognition.tsv"
    tsv.write_text("", encoding="utf-8")

    assert builder._resolve_deck_name(
        tsv,
        "Japanese Grammar::13 - L1 Interference::Recognition",
    ) == "Japanese Grammar::13 - L1 Interference::English::Recognition"


def test_resolve_l1_deck_name_preserves_language_specific_path(tmp_path):
    l1_dir = tmp_path / "13-l1"
    l1_dir.mkdir()
    tsv = l1_dir / "l1-pronoun-overuse_recognition.tsv"
    tsv.write_text("", encoding="utf-8")

    deck = "Japanese Grammar::13 - L1 Interference::English::Recognition"
    assert builder._resolve_deck_name(tsv, deck) == deck


def test_deck_option_key_routes_note_types_and_l1():
    assert builder._deck_option_key("Default") == "default"
    assert builder._deck_option_key("Japanese Grammar") == "root"
    assert (
        builder._deck_option_key("Japanese Grammar::01 - N5 Grammar::02 · Production")
        == "production"
    )
    assert (
        builder._deck_option_key(
            "Japanese Grammar::13 - L1 Interference::English::01 · Recognition"
        )
        == "l1_recognition"
    )
    assert (
        builder._deck_option_key("Japanese Grammar::13 - L1 Interference::English")
        == "l1_parent"
    )
