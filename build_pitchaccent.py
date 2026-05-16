#!/usr/bin/env python3
"""
Reliable pitch-accent index builder.

Goals:
  - deterministic multi-source merge
  - explicit confidence tiers
  - override-first curation workflow
  - coverage gating for release pipelines

Source priority:
  1. overrides (manual curation)
  2. Kanjium sqlite
  3. NHK CSV

Outputs:
  - media/pitchaccent_index.json
  - research-reports/pitchaccent_coverage_report.md
"""
from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Optional

WORDS_PATH = Path("media/words_index.json")
OUT_PATH = Path("media/pitchaccent_index.json")
REPORT_PATH = Path("research-reports/pitchaccent_coverage_report.md")
DATA_DIR = Path("data")
OVERRIDES_PATH = Path("data/pitch-accent/overrides.json")

INDEX_VERSION = 2


def _to_hiragana(s: str) -> str:
    if not s:
        return ""
    out = []
    for ch in s:
        code = ord(ch)
        # Katakana -> Hiragana block shift
        if 0x30A1 <= code <= 0x30F6:
            out.append(chr(code - 0x60))
        else:
            out.append(ch)
    return "".join(out)


def _normalize_token(token: str) -> str:
    token = unicodedata.normalize("NFKC", token.strip())
    # Keep Japanese letters only for lookup consistency.
    cleaned = "".join(ch for ch in token if _is_japanese_char(ch))
    return cleaned or token


def _is_japanese_char(ch: str) -> bool:
    return (
        ("\u3040" <= ch <= "\u309f")  # hiragana
        or ("\u30a0" <= ch <= "\u30ff")  # katakana
        or ("\u4e00" <= ch <= "\u9fff")  # kanji
        or ch == "ー"
    )


def _is_lexical_token(token: str) -> bool:
    token = _normalize_token(token)
    if not token:
        return False
    # Exclude 1-char pure hiragana particles/aux noise from reliability KPI.
    if len(token) == 1 and all("\u3040" <= ch <= "\u309f" for ch in token):
        return False
    return True


def _reading_mora_count(reading: str) -> int:
    moras = []
    for ch in reading:
        if ch in "ゃゅょャュョ" and moras:
            moras[-1] += ch
        else:
            moras.append(ch)
    return len(moras)


def _accent_to_pattern(reading: str, accent: int) -> str:
    """Convert Tokyo accent number → coarse L/H mora-by-mora pattern.

      accent = 0 → heiban   (LHHH…)
      accent = 1 → atamadaka(HLLL…)
      accent = N → nakadaka, drop after the N-th mora.

    Counts "mora" as kana characters minus standalone yō-on (ゃゅょ),
    which attach to the previous mora. Long vowels and っ each count
    as one mora.
    """
    moras = []
    for ch in reading:
        if ch in "ゃゅょャュョ" and moras:
            moras[-1] += ch
        else:
            moras.append(ch)
    n = len(moras)
    if n == 0:
        return ""
    if accent == 0:
        return "L" + "H" * (n - 1)
    if accent == 1:
        return "H" + "L" * (n - 1)
    return "L" + "H" * (accent - 1) + "L" * (n - accent)


def _normalize_reading(reading: str) -> str:
    return _to_hiragana(unicodedata.normalize("NFKC", reading.strip()))


def _parse_int(s: str) -> Optional[int]:
    s = s.strip()
    if not s:
        return None
    if s.isdigit():
        return int(s)
    return None


def _accent_in_range(accent: int, reading: str) -> bool:
    m = _reading_mora_count(reading)
    return 0 <= accent <= m


def _iter_candidate_keys(token: str) -> Iterable[str]:
    token = _normalize_token(token)
    if not token:
        return []
    keys = {token, _to_hiragana(token)}
    # Remove braces and parenthetical hints if present in tokenized vocab.
    if "(" in token and ")" in token:
        keys.add(token.split("(", 1)[0].strip())
    for c in _deinflect_candidates(token):
        keys.add(c)
        keys.add(_to_hiragana(c))
    # Longest-first lookup helps prefer full dictionary forms over short particles.
    return sorted([k for k in keys if k], key=len, reverse=True)


def _deinflect_candidates(token: str) -> list[str]:
    """Return heuristic dictionary-form candidates for conjugated tokens.

    This is intentionally conservative-but-broad: it emits multiple candidates for
    ambiguous godan endings and lets source lookups choose valid hits.
    """
    t = _normalize_token(token)
    out = {t}

    # Common polite/auxiliary tails.
    tail_rules = [
        ("ませんでした", "る"),
        ("ません", "る"),
        ("ました", "る"),
        ("たいです", "る"),
        ("たくない", "る"),
        ("たかった", "る"),
        ("ないです", "る"),
        ("なかった", "る"),
        ("なくて", "る"),
        ("ない", "る"),
        ("られた", "る"),
        ("られる", "る"),
        ("させた", "す"),
        ("させる", "す"),
    ]
    for old, new in tail_rules:
        if t.endswith(old) and len(t) > len(old):
            out.add(t[: -len(old)] + new)

    # i-adjective conjugations.
    iadj_rules = [
        ("くなかった", "い"),
        ("かった", "い"),
        ("くない", "い"),
        ("くて", "い"),
    ]
    for old, new in iadj_rules:
        if t.endswith(old) and len(t) > len(old):
            out.add(t[: -len(old)] + new)

    # Irregulars.
    irr = {
        "した": "する",
        "して": "する",
        "しない": "する",
        "しなかった": "する",
        "きた": "くる",
        "きて": "くる",
        "こない": "くる",
        "こなかった": "くる",
    }
    if t in irr:
        out.add(irr[t])

    # Godan/ichidan plain past -> dictionary candidates.
    past_rules = [
        ("った", ["う", "つ", "る"]),
        ("んだ", ["む", "ぶ", "ぬ"]),
        ("いた", ["く"]),
        ("いだ", ["ぐ"]),
        ("した", ["す"]),
        ("た", ["る"]),   # ichidan-style fallback
        ("て", ["る"]),   # ichidan-style fallback
    ]
    te_rules = [
        ("って", ["う", "つ", "る"]),
        ("んで", ["む", "ぶ", "ぬ"]),
        ("いて", ["く"]),
        ("いで", ["ぐ"]),
        ("して", ["す"]),
    ]
    for old, news in past_rules + te_rules:
        if t.endswith(old) and len(t) > len(old):
            stem = t[: -len(old)]
            for n in news:
                out.add(stem + n)

    # Keep candidate set bounded to avoid noisy lookups.
    candidates = [c for c in out if c and c != token]
    candidates = sorted(set(candidates), key=len, reverse=True)
    return candidates[:24]


def _load_overrides() -> dict[str, dict]:
    if not OVERRIDES_PATH.exists():
        return {}
    try:
        raw = json.loads(OVERRIDES_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    out: dict[str, dict] = {}
    for token, v in raw.items():
        try:
            reading = _normalize_reading(v["reading"])
            accent = int(v["accent"])
            if not _accent_in_range(accent, reading):
                continue
            out[_normalize_token(token)] = {
                "reading": reading,
                "accent": str(accent),
                "pattern": _accent_to_pattern(reading, accent),
                "source": "override",
            }
        except Exception:
            continue
    return out


def _load_kanjium_index() -> dict[str, list[dict]]:
    db = DATA_DIR / "accents.sqlite"
    if not db.exists():
        db = DATA_DIR / "pitch-accent/accents.sqlite"
    if not db.exists():
        return {}
    out: dict[str, list[dict]] = defaultdict(list)
    try:
        con = sqlite3.connect(db)
        cur = con.execute("SELECT expression, reading, accent FROM accents")
        for expr, reading, accent in cur:
            expr_n = _normalize_token(str(expr))
            reading_n = _normalize_reading(str(reading))
            try:
                accent_i = int(accent)
            except Exception:
                continue
            if not expr_n or not reading_n or not _accent_in_range(accent_i, reading_n):
                continue
            rec = {
                "reading": reading_n,
                "accent": str(accent_i),
                "pattern": _accent_to_pattern(reading_n, accent_i),
                "source": "kanjium",
            }
            out[expr_n].append(rec)
            out[_to_hiragana(expr_n)].append(rec)
            out[reading_n].append(rec)
        con.close()
    except sqlite3.DatabaseError:
        return {}
    return out


def _pick_nhk_accent(row: list[str], reading: str) -> Optional[int]:
    # ACCDB_unicode.csv variants put accent candidates around columns 9/10.
    # Fallback: scan all integer-like columns and choose first valid value.
    candidates = []
    for idx in (10, 9):
        if idx < len(row):
            v = _parse_int(row[idx])
            if v is not None:
                candidates.append(v)
    if not candidates:
        for cell in row:
            v = _parse_int(cell)
            if v is not None:
                candidates.append(v)
    for c in candidates:
        if _accent_in_range(c, reading):
            return c
    return None


def _load_nhk_index() -> dict[str, list[dict]]:
    candidates = [
        DATA_DIR / "pitch-accent/nhk_accents.csv",
        DATA_DIR / "nhk_accents.csv",
    ]
    csv_path = next((p for p in candidates if p.exists()), None)
    if csv_path is None:
        return {}
    out: dict[str, list[dict]] = defaultdict(list)
    with csv_path.open(encoding="utf-8", newline="") as fh:
        r = csv.reader(fh)
        for row in r:
            if len(row) < 9:
                continue
            # Heuristic columns based on dataset shape:
            # [6]=kana reading, [7]=written form, [8]=annotated form
            reading = _normalize_reading(row[6] if len(row) > 6 else "")
            written = _normalize_token(row[7] if len(row) > 7 else "")
            annotated = _normalize_token(row[8] if len(row) > 8 else "")
            if not reading:
                continue
            accent = _pick_nhk_accent(row, reading)
            if accent is None:
                continue
            rec = {
                "reading": reading,
                "accent": str(accent),
                "pattern": _accent_to_pattern(reading, accent),
                "source": "nhk",
            }
            for k in {written, annotated, _to_hiragana(written), _to_hiragana(annotated), reading}:
                if k:
                    out[k].append(rec)
    return out


def _dedupe_records(records: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for r in records:
        k = (r["source"], r["reading"], r["accent"])
        if k in seen:
            continue
        seen.add(k)
        out.append(r)
    return out


def _resolve_token(token: str, overrides: dict[str, dict],
                   kanjium: dict[str, list[dict]],
                   nhk: dict[str, list[dict]]) -> tuple[Optional[dict], dict]:
    keys = list(_iter_candidate_keys(token))
    meta = {"sources": [], "conflict": False}

    for k in keys:
        if k in overrides:
            picked = dict(overrides[k])
            picked["confidence"] = "high"
            picked["sources_considered"] = ["override"]
            return picked, meta

    candidates = []
    for k in keys:
        candidates.extend(kanjium.get(k, []))
    for k in keys:
        candidates.extend(nhk.get(k, []))
    candidates = _dedupe_records(candidates)
    if not candidates:
        return None, meta

    by_source: dict[str, list[dict]] = defaultdict(list)
    for c in candidates:
        by_source[c["source"]].append(c)
    meta["sources"] = sorted(by_source.keys())

    # deterministic priority pick
    priority = ("kanjium", "nhk")
    picked = None
    for src in priority:
        if by_source.get(src):
            picked = by_source[src][0]
            break
    if picked is None:
        picked = candidates[0]

    # confidence: high if at least 2 sources agree on accent+reading
    signature_counts: dict[tuple[str, str], set[str]] = defaultdict(set)
    for c in candidates:
        signature_counts[(c["reading"], c["accent"])].add(c["source"])
    best_sig = (picked["reading"], picked["accent"])
    if len(signature_counts[best_sig]) >= 2:
        conf = "high"
    else:
        conf = "medium"
    if len(signature_counts) > 1:
        meta["conflict"] = True
    out = dict(picked)
    out["confidence"] = conf
    out["sources_considered"] = sorted(meta["sources"])
    return out, meta


def _write_report(total: int, covered: int, weighted_total: int, weighted_covered: int,
                  lexical_total: int, lexical_covered: int,
                  lexical_weighted_total: int, lexical_weighted_covered: int,
                  entries: dict[str, dict], missing: list[str], conflicts: list[str],
                  source_hits: dict[str, int], words: dict[str, int]) -> None:
    coverage = (covered / total * 100.0) if total else 0.0
    weighted_coverage = (weighted_covered / weighted_total * 100.0) if weighted_total else 0.0
    lexical_coverage = (lexical_covered / lexical_total * 100.0) if lexical_total else 0.0
    lexical_weighted_coverage = (
        lexical_weighted_covered / lexical_weighted_total * 100.0
    ) if lexical_weighted_total else 0.0
    confidence_counts = defaultdict(int)
    for e in entries.values():
        confidence_counts[e.get("confidence", "unknown")] += 1
    missing_top = sorted(missing, key=lambda t: words.get(t, 0), reverse=True)
    conflict_top = sorted(conflicts, key=lambda t: words.get(t, 0), reverse=True)
    lines = [
        "# Pitch Accent Coverage Report",
        "",
        f"- Total tokens: **{total}**",
        f"- Covered tokens: **{covered}**",
        f"- Coverage: **{coverage:.2f}%**",
        f"- Weighted coverage (by token frequency): **{weighted_coverage:.2f}%**",
        f"- Lexical coverage (filtered tokens): **{lexical_coverage:.2f}%**",
        f"- Lexical weighted coverage: **{lexical_weighted_coverage:.2f}%**",
        "",
        "## Confidence",
        "",
        f"- high: {confidence_counts['high']}",
        f"- medium: {confidence_counts['medium']}",
        "",
        "## Source Hits",
        "",
    ]
    for src, n in sorted(source_hits.items()):
        lines.append(f"- {src}: {n}")
    lines += ["", f"## Conflict Queue ({len(conflicts)})", ""]
    for t in conflict_top[:100]:
        lines.append(f"- {t} (count={words.get(t, 0)})")
    lines += [
        "",
        f"## Missing Queue ({len(missing)})",
        "",
    ]
    for t in missing_top[:200]:
        lines.append(f"- {t} (count={words.get(t, 0)})")
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ── Driver ───────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser(description="Build reliable per-token pitch-accent index")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--min-coverage", type=float, default=0.0,
                    help="Fail if coverage falls below this percentage")
    ap.add_argument("--strict", action="store_true",
                    help="Fail when conflicts or missing queue is non-empty")
    ap.add_argument("--report-missing", action="store_true",
                    help="Print every token with no source hit")
    args = ap.parse_args()

    if not WORDS_PATH.exists():
        print(f"{WORDS_PATH} not found — run build_furigana.py first.")
        return 1

    words = json.loads(WORDS_PATH.read_text(encoding="utf-8")).get("tokens", {})
    tokens = list(words.keys())
    if args.limit:
        tokens = tokens[:args.limit]

    overrides = _load_overrides()
    kanjium = _load_kanjium_index()
    nhk = _load_nhk_index()

    entries: dict[str, dict] = {}
    missing: list[str] = []
    conflicts: list[str] = []
    source_hits: dict[str, int] = defaultdict(int)
    for t in tokens:
        hit, meta = _resolve_token(t, overrides, kanjium, nhk)
        if hit:
            entries[t] = hit
            source_hits[hit.get("source", "unknown")] += 1
            if meta.get("conflict"):
                conflicts.append(t)
        else:
            missing.append(t)

    covered = len(entries)
    weighted_total = sum(int(v) for v in words.values() if isinstance(v, int))
    weighted_covered = sum(int(words.get(k, 0)) for k in entries.keys())
    lexical_tokens = [t for t in tokens if _is_lexical_token(t)]
    lexical_total = len(lexical_tokens)
    lexical_covered = sum(1 for t in lexical_tokens if t in entries)
    lexical_weighted_total = sum(int(words.get(t, 0)) for t in lexical_tokens)
    lexical_weighted_covered = sum(int(words.get(t, 0)) for t in lexical_tokens if t in entries)
    coverage = (covered / len(tokens) * 100.0) if tokens else 0.0
    weighted_coverage = (weighted_covered / weighted_total * 100.0) if weighted_total else 0.0
    lexical_coverage = (lexical_covered / lexical_total * 100.0) if lexical_total else 0.0
    lexical_weighted_coverage = (
        lexical_weighted_covered / lexical_weighted_total * 100.0
    ) if lexical_weighted_total else 0.0
    _write_report(
        len(tokens), covered, weighted_total, weighted_covered,
        lexical_total, lexical_covered, lexical_weighted_total, lexical_weighted_covered,
        entries, missing, conflicts, source_hits, words
    )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(
        json.dumps({"version": INDEX_VERSION,
                    "entries": entries,
                    "coverage_percent": round(coverage, 4),
                    "weighted_coverage_percent": round(weighted_coverage, 4),
                    "lexical_coverage_percent": round(lexical_coverage, 4),
                    "lexical_weighted_coverage_percent": round(lexical_weighted_coverage, 4),
                    "conflicts_count": len(conflicts),
                    "missing_count": len(missing),
                    "missing": missing[:200] if args.report_missing else []},
                   indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"✓ Pitch-accent index → {OUT_PATH} "
          f"({covered}/{len(tokens)} tokens, "
          f"{len(missing)} missing, {len(conflicts)} conflicts, "
          f"coverage={coverage:.2f}%, weighted={weighted_coverage:.2f}%, "
          f"lexical={lexical_coverage:.2f}%/{lexical_weighted_coverage:.2f}%)")
    if not entries:
        print("  (no source data under data/ — see header docstring)")
    if args.min_coverage and coverage < args.min_coverage:
        print(f"✗ Coverage gate failed: {coverage:.2f}% < {args.min_coverage:.2f}%")
        return 2
    if args.strict and (missing or conflicts):
        print(f"✗ Strict gate failed: missing={len(missing)} conflicts={len(conflicts)}")
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
