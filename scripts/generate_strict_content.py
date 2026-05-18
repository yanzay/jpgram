#!/usr/bin/env python3
"""
Replace scaffold:pending-content rows in grammar-strict/ with authored
sentences.

Reads a content data file (JSON or Python module) describing, per point
slug, 5 example sentences plus card-level metadata (Label/Formula/MainUse/
QuickCue/Contrast/Why). For each slug it rewrites the recognition.tsv
and production.tsv files for that point with the new rows, generating
hiragana Reading via scripts.jp_reading and audio hash via sha1[:12].

Tags:
  - scaffold:pending-content is dropped (we have real content now).
  - scaffold:pending-audio is RETAINED until build_audio.py renders the
    corresponding mp3; another pass strips it once audio exists on disk.
  - source:authored is added.

Usage:
  python scripts/generate_strict_content.py \
      --content content/n5_strict_content.json \
      --module 01-n5
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
ROOT = SCRIPTS_DIR.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from jp_reading import reading  # noqa: E402
from grammar_reference import filename_safe_slug  # noqa: E402

MODULE_LABELS = {
    "01-n5": "01 - N5 Grammar",
    "02-n4": "02 - N4 Grammar",
    "03-n3": "03 - N3 Grammar",
    "04-n2": "04 - N2 Grammar",
    "05-n1": "05 - N1 Grammar",
}

MODULE_JLPT = {
    "01-n5": "n5",
    "02-n4": "n4",
    "03-n3": "n3",
    "04-n2": "n2",
    "05-n1": "n1",
}

RECOGNITION_HEADER = (
    "#separator:tab",
    "#html:true",
    "#columns:JP\tReading\tEN\tLabel\tFormula\tMainUse\tQuickCue\tContrast\tAudio\tTags",
    "#notetype:Recognition",
)

PRODUCTION_HEADER = (
    "#separator:tab",
    "#html:true",
    "#columns:Prompt\tTarget\tReading\tSample\tWhy\tAudio\tTags",
    "#notetype:Production",
)


def audio_tag(text: str) -> str:
    h = hashlib.sha1(text.strip().encode("utf-8")).hexdigest()[:12]
    return f"[sound:{h}.mp3]"


def build_tags(*, module: str, jlpt: str, slug: str, extra: list[str] | None = None) -> str:
    parts = [
        f"module:{module}",
        f"jlpt:{jlpt}",
        f"point:{slug}",
        "source:authored",
        "scaffold:pending-audio",
    ]
    if extra:
        parts.extend(extra)
    return " ".join(parts)


def write_recognition(path: Path, *, module: str, slug: str, entry: dict) -> None:
    deck_label = MODULE_LABELS[module]
    jlpt = MODULE_JLPT[module]
    label = entry.get("label", entry.get("title", slug))
    formula = entry.get("formula", "")
    main_use = entry.get("main_use", "")
    contrast_field = entry.get("contrast", "")

    lines: list[str] = list(RECOGNITION_HEADER) + [
        f"#deck:Japanese Grammar (Strict)::{deck_label}::Recognition",
        "",
    ]
    for s in entry["sentences"]:
        jp = s["jp"].strip()
        row = [
            jp,
            reading(jp),
            s.get("en", "").strip(),
            s.get("label", label),
            s.get("formula", formula),
            s.get("main_use", main_use),
            s.get("quick_cue", ""),
            s.get("contrast", contrast_field),
            audio_tag(jp),
            build_tags(module=module, jlpt=jlpt, slug=slug, extra=s.get("tags")),
        ]
        lines.append("\t".join(row))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_production(path: Path, *, module: str, slug: str, entry: dict) -> None:
    deck_label = MODULE_LABELS[module]
    jlpt = MODULE_JLPT[module]
    main_use = entry.get("main_use", "")

    lines: list[str] = list(PRODUCTION_HEADER) + [
        f"#deck:Japanese Grammar (Strict)::{deck_label}::Production",
        "",
    ]
    for s in entry["sentences"]:
        jp = s["jp"].strip()
        prompt = s.get("prompt") or s.get("en", "").strip()
        why = s.get("why") or s.get("quick_cue") or main_use
        row = [
            prompt,
            jp,
            reading(jp),
            jp,
            why,
            audio_tag(jp),
            build_tags(module=module, jlpt=jlpt, slug=slug, extra=s.get("tags")),
        ]
        lines.append("\t".join(row))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_content(path: Path) -> dict:
    if path.suffix == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    if path.suffix == ".py":
        spec = importlib.util.spec_from_file_location("content_data", path)
        mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
        assert spec and spec.loader
        spec.loader.exec_module(mod)
        if not hasattr(mod, "CONTENT"):
            raise SystemExit(f"{path}: expected module-level CONTENT dict")
        return mod.CONTENT
    raise SystemExit(f"unsupported content file: {path}")


def validate_entry(slug: str, entry: dict) -> list[str]:
    errors: list[str] = []
    sentences = entry.get("sentences", [])
    if len(sentences) != 5:
        errors.append(f"{slug}: expected exactly 5 sentences, got {len(sentences)}")
    for i, s in enumerate(sentences, 1):
        if not s.get("jp", "").strip():
            errors.append(f"{slug}#{i}: missing jp")
        if not s.get("en", "").strip():
            errors.append(f"{slug}#{i}: missing en")
    return errors


def has_pending_scaffold(path: Path) -> bool:
    """True if `path` exists and contains scaffold:pending-content tags."""
    if not path.exists():
        return False
    return "scaffold:pending-content" in path.read_text(encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--content", required=True, type=Path)
    ap.add_argument("--module", required=True, choices=list(MODULE_LABELS))
    ap.add_argument("--only", action="append", help="Restrict to specific slug(s)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--force",
        action="store_true",
        help="Overwrite even when file lacks scaffold:pending-content "
             "(use to repair existing real content). Off by default for safety.",
    )
    args = ap.parse_args()

    content = load_content(args.content)
    if not isinstance(content, dict):
        raise SystemExit(f"{args.content}: expected dict at top level")

    grammar_dir = ROOT / "grammar-strict" / args.module
    if not grammar_dir.exists():
        raise SystemExit(f"missing grammar dir: {grammar_dir}")

    targets = sorted(content.keys()) if not args.only else [s for s in args.only if s in content]
    print(f"module={args.module} content_slugs={len(content)} targets={len(targets)}")

    errs: list[str] = []
    for slug in targets:
        entry = content[slug]
        errs.extend(validate_entry(slug, entry))
    if errs:
        for e in errs:
            print(f"  ERROR: {e}")
        return 2

    written = 0
    skipped: list[str] = []
    for slug in targets:
        safe = filename_safe_slug(slug)
        rec = grammar_dir / f"{safe}_recognition.tsv"
        pro = grammar_dir / f"{safe}_production.tsv"
        entry = content[slug]
        if not args.force:
            rec_safe = (not rec.exists()) or has_pending_scaffold(rec)
            pro_safe = (not pro.exists()) or has_pending_scaffold(pro)
            if not (rec_safe and pro_safe):
                skipped.append(slug)
                print(f"  skip {slug} (real content present; use --force to override)")
                continue
        if args.dry_run:
            print(f"  [dry-run] would write {rec.name} + {pro.name}")
            continue
        write_recognition(rec, module=args.module, slug=slug, entry=entry)
        write_production(pro, module=args.module, slug=slug, entry=entry)
        written += 2
        print(f"  wrote {rec.relative_to(ROOT)}")
        print(f"  wrote {pro.relative_to(ROOT)}")

    print(f"\n✓ done. files_written={written} skipped={len(skipped)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
