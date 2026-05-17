#!/usr/bin/env python3
"""
Scaffold recognition + production TSVs in grammar-strict/ for Bunpro points
that have taxonomy rows but no cards yet.

Uses existing manifest audio as a temporary stub; tag rows with scaffold:pending-content.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
from grammar_reference import (  # noqa: E402
    LEVEL_TO_MODULE,
    ROOT,
    filename_safe_slug,
    load_taxonomy_rows,
    parse_bunpro_id,
    strict_deck_paths,
)

MANIFEST_PATH = ROOT / "media/audio_manifest.json"
STUB_AUDIO = "[sound:a971a68f1a9d.mp3]"
SENTENCES_PER_FILE = 5

MODULE_LABEL = {
    "01-n5": "01 - N5 Grammar",
    "02-n4": "02 - N4 Grammar",
    "03-n3": "03 - N3 Grammar",
    "04-n2": "04 - N2 Grammar",
    "05-n1": "05 - N1 Grammar",
}


def stub_audio() -> str:
    if MANIFEST_PATH.exists():
        entries = json.loads(MANIFEST_PATH.read_text(encoding="utf-8")).get("entries", {})
        if entries:
            key = next(iter(entries))
            return f"[sound:{key}.mp3]"
    return STUB_AUDIO


def level_to_module(level: str) -> tuple[str, str, str]:
    module, jlpt = LEVEL_TO_MODULE.get(level, ("12-beyond-n1", ""))
    label = MODULE_LABEL.get(module, module)
    return module, jlpt, label


def has_cards(grammar_dir: Path, module: str, point_slug: str) -> bool:
    safe = filename_safe_slug(point_slug)
    mod = grammar_dir / module
    if not mod.exists():
        return False
    return any(mod.glob(f"{safe}_*.tsv"))


def write_recognition(
    path: Path,
    *,
    deck_label: str,
    point_slug: str,
    module: str,
    jlpt: str,
    title: str,
    meaning: str,
    audio: str,
) -> None:
    lines = [
        "#separator:tab",
        "#html:true",
        "#columns:JP\tReading\tEN\tLabel\tFormula\tMainUse\tQuickCue\tContrast\tAudio\tTags",
        "#notetype:Recognition",
        f"#deck:Japanese Grammar (Strict)::{deck_label}::Recognition",
        "",
    ]
    for i in range(1, SENTENCES_PER_FILE + 1):
        jp = f"（{title}）を使う例文{i}です。"
        reading = ""
        en = meaning or f"Example for {title}"
        tags = (
            f"module:{module} jlpt:{jlpt} point:{point_slug} "
            f"scaffold:pending-content scaffold:pending-audio source:bunpro"
        )
        row = [
            jp,
            reading,
            en,
            title,
            title,
            meaning or "See Bunpro",
            "Scaffold",
            "",
            audio,
            tags,
        ]
        lines.append("\t".join(row))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_production(
    path: Path,
    *,
    deck_label: str,
    point_slug: str,
    module: str,
    jlpt: str,
    title: str,
    meaning: str,
    audio: str,
) -> None:
    lines = [
        "#separator:tab",
        "#html:true",
        "#columns:Prompt\tTarget\tReading\tSample\tWhy\tAudio\tTags",
        "#notetype:Production",
        f"#deck:Japanese Grammar (Strict)::{deck_label}::Production",
        "",
    ]
    for i in range(1, SENTENCES_PER_FILE + 1):
        prompt = f"Say: example {i} using {title}"
        target = f"（{title}）の例文{i}です。"
        tags = (
            f"module:{module} jlpt:{jlpt} point:{point_slug} "
            f"scaffold:pending-content scaffold:pending-audio source:bunpro"
        )
        row = [prompt, target, "", target, meaning or "Scaffold", audio, tags]
        lines.append("\t".join(row))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--level",
        action="append",
        required=True,
        help="Bunpro level(s), e.g. JLPT5 (repeatable).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print counts only; do not write files.",
    )
    args = parser.parse_args()

    strict_taxonomy, grammar_dir, _ = strict_deck_paths()
    rows = load_taxonomy_rows(strict_taxonomy)
    audio = stub_audio()

    # Load bunpro metadata for titles
    bunpro_meta: dict[str, dict] = {}
    live_path = ROOT / "data/grammar-refs/bunpro_live_index.json"
    if live_path.exists():
        for p in json.loads(live_path.read_text(encoding="utf-8"))["points"]:
            bunpro_meta[p["slug"]] = p

    targets: list[dict[str, str]] = []
    for row in rows:
        status, slug = parse_bunpro_id(row["bunpro_id"])
        if status != "resolved":
            continue
        meta = bunpro_meta.get(slug, {})
        level = str(meta.get("level", ""))
        if level not in args.level:
            continue
        module, jlpt, deck_label = level_to_module(level)
        if row["module"] != module:
            module = row["module"]
        if has_cards(grammar_dir, module, row["point_slug"]):
            continue
        targets.append(
            {
                "point_slug": row["point_slug"],
                "module": module,
                "jlpt": jlpt or row["jlpt"],
                "deck_label": deck_label,
                "title": str(meta.get("title", slug)),
                "meaning": str(meta.get("meaning", "")),
            }
        )

    written = 0
    for t in targets:
        safe = filename_safe_slug(t["point_slug"])
        mod_dir = grammar_dir / t["module"]
        rec = mod_dir / f"{safe}_recognition.tsv"
        pro = mod_dir / f"{safe}_production.tsv"
        if args.dry_run:
            continue
        mod_dir.mkdir(parents=True, exist_ok=True)
        write_recognition(
            rec,
            deck_label=t["deck_label"],
            point_slug=t["point_slug"],
            module=t["module"],
            jlpt=t["jlpt"],
            title=t["title"],
            meaning=t["meaning"],
            audio=audio,
        )
        write_production(
            pro,
            deck_label=t["deck_label"],
            point_slug=t["point_slug"],
            module=t["module"],
            jlpt=t["jlpt"],
            title=t["title"],
            meaning=t["meaning"],
            audio=audio,
        )
        written += 2

    print(f"level={args.level} targets={len(targets)} files_written={written} dry_run={args.dry_run}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
