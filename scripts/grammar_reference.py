#!/usr/bin/env python3
"""Shared loaders and Bunpro ID parsing for grammar-completeness tooling."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
TAXONOMY_PATH = ROOT / "data" / "grammar_taxonomy.tsv"
BUNPRO_LIVE_PATH = ROOT / "data" / "grammar-refs" / "bunpro_live_index.json"
REFERENCE_CLOSURE_PATH = ROOT / "data" / "grammar-refs" / "reference_closure.json"

LEVEL_TO_MODULE = {
    "JLPT5": ("01-n5", "n5"),
    "JLPT4": ("02-n4", "n4"),
    "JLPT3": ("03-n3", "n3"),
    "JLPT2": ("04-n2", "n2"),
    "JLPT1": ("05-n1", "n1"),
}

EXEMPT_MODULE = {
    "writing-system": ("00-foundation", "n5"),
    "pitch-accent": ("00-foundation", "n5"),
    "onomatopoeia": ("10-onomatopoeia", ""),
    "l1-interference": ("13-l1", ""),
}


def strict_deck_paths(closure: dict[str, Any] | None = None) -> tuple[Path, Path, Path]:
    closure = closure or load_reference_closure()
    deck = closure["strict_deck"]
    taxonomy = ROOT / deck["taxonomy_path"]
    grammar = ROOT / deck["grammar_dir"]
    manifest = ROOT / deck["manifest_path"]
    return taxonomy, grammar, manifest


def filename_safe_slug(point_slug: str) -> str:
    """Filesystem-safe stem; point:* tags keep the original slug."""
    out = point_slug.strip()
    for ch in ("/", ":", "\\", "|", "?", "*"):
        out = out.replace(ch, "-")
    return out or "point"


def load_reference_closure() -> dict[str, Any]:
    if not REFERENCE_CLOSURE_PATH.exists():
        raise FileNotFoundError(f"missing reference closure: {REFERENCE_CLOSURE_PATH}")
    return json.loads(REFERENCE_CLOSURE_PATH.read_text(encoding="utf-8"))


def exemption_map(closure: dict[str, Any] | None = None) -> dict[str, str]:
    closure = closure or load_reference_closure()
    out: dict[str, str] = {}
    for row in closure.get("taxonomy_exemptions", []):
        slug = str(row.get("point_slug", "")).strip()
        exempt_id = str(row.get("exempt_id", "")).strip()
        if slug and exempt_id:
            out[slug] = exempt_id
    return out


def normalize_bucket_slugs(closure: dict[str, Any] | None = None) -> set[str]:
    closure = closure or load_reference_closure()
    return {
        str(row.get("point_slug", "")).strip()
        for row in closure.get("taxonomy_normalize_buckets", [])
        if str(row.get("point_slug", "")).strip()
    }


def parse_bunpro_id(bunpro_id: str) -> tuple[str, str]:
    """
    Returns (status, normalized_slug_or_reason).

    status: auto | missing | malformed | resolved | exempt
    """
    value = bunpro_id.strip()
    if not value:
        return "missing", ""
    if value.startswith("bunpro:auto/"):
        return "auto", value.split("bunpro:auto/", 1)[1].strip()
    if not value.startswith("bunpro:"):
        return "malformed", ""
    payload = value.split("bunpro:", 1)[1].strip()
    if not payload:
        return "malformed", ""
    if payload.startswith("exempt/"):
        return "exempt", payload.split("exempt/", 1)[1].strip()
    normalized = payload.split("/")[-1].strip()
    if not normalized:
        return "malformed", ""
    return "resolved", normalized


def load_taxonomy_rows(taxonomy_path: Path | None = None) -> list[dict[str, str]]:
    path = taxonomy_path or TAXONOMY_PATH
    rows: list[dict[str, str]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw or raw.startswith("#"):
            continue
        row = next(csv.reader([raw], delimiter="\t", quotechar='"'))
        while len(row) < 9:
            row.append("")
        rows.append(
            {
                "point_slug": row[0].strip(),
                "jlpt": row[1].strip(),
                "module": row[2].strip(),
                "bunpro_id": row[3].strip(),
                "tofugu_url": row[4].strip(),
                "imabi_url": row[5].strip(),
                "shinkanzen_ref": row[6].strip(),
                "djg_page": row[7].strip(),
                "notes": row[8].strip(),
            }
        )
    return rows


def load_bunpro_live_points() -> list[dict[str, Any]]:
    if not BUNPRO_LIVE_PATH.exists():
        raise FileNotFoundError(f"missing Bunpro snapshot: {BUNPRO_LIVE_PATH}")
    return json.loads(BUNPRO_LIVE_PATH.read_text(encoding="utf-8"))["points"]


def taxonomy_bunpro_slug_index(
    taxonomy_rows: list[dict[str, str]],
) -> dict[str, list[str]]:
    """Map Bunpro slug -> taxonomy point_slugs that reference it."""
    index: dict[str, list[str]] = {}
    for row in taxonomy_rows:
        status, slug = parse_bunpro_id(row["bunpro_id"])
        if status != "resolved" or not slug:
            continue
        index.setdefault(slug, []).append(row["point_slug"])
    return index
