#!/usr/bin/env python3
"""
Build candidate Bunpro mappings for unresolved taxonomy points.

Does NOT mutate taxonomy. It emits ranked candidates for manual curation.
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
TAXONOMY = ROOT / "data/grammar_taxonomy.tsv"
GRAMMAR = ROOT / "grammar"
BUNPRO = ROOT / "data/grammar-refs/bunpro_live_index.json"
OUT_JSON = ROOT / "research-reports/bunpro_mapping_candidates.json"
OUT_MD = ROOT / "research-reports/bunpro_mapping_candidates.md"

JP_TOKEN_RE = re.compile(r"[一-龯ぁ-んァ-ンー〜～]+")

# Tokens that are too broad to be useful mapping anchors.
STOP = {
    "に", "で", "と", "が", "を", "は", "も", "の", "な", "だ", "ます", "する", "ある",
    "いる", "か", "て", "から", "ので", "だけ", "こと", "もの", "ところ", "よう", "そう",
}


def detect_note_type(path: Path) -> str:
    stem = path.stem
    for nt in ("recognition", "production", "cloze", "contrast", "listening", "dictation"):
        if stem.endswith(f"_{nt}"):
            return nt
    return "unknown"


def parse_tsv(path: Path):
    lines = path.read_text(encoding="utf-8").splitlines()
    header = None
    rows = []
    for ln in lines:
        if ln.startswith("#columns:"):
            header = ln[len("#columns:") :].split("\t")
            continue
        if not ln or ln.startswith("#"):
            continue
        row = next(csv.reader([ln], delimiter="\t", quotechar='"'))
        if header and len(row) == len(header):
            rows.append(row)
    return header, rows


def main() -> int:
    bunpro = json.loads(BUNPRO.read_text(encoding="utf-8"))["points"]
    bunpro_expr = {p["slug"] for p in bunpro} | {p["title"] for p in bunpro}

    unresolved = []
    for raw in TAXONOMY.read_text(encoding="utf-8").splitlines():
        if not raw or raw.startswith("#"):
            continue
        r = next(csv.reader([raw], delimiter="\t", quotechar='"'))
        while len(r) < 9:
            r.append("")
        if r[3].startswith("bunpro:auto/") or not r[3]:
            unresolved.append({"point_slug": r[0], "module": r[2], "jlpt": r[1], "bunpro_id": r[3]})

    unresolved_points = {u["point_slug"] for u in unresolved}
    token_counts: dict[str, Counter[str]] = defaultdict(Counter)

    for path in GRAMMAR.rglob("*.tsv"):
        nt = detect_note_type(path)
        if nt not in {"recognition", "production", "cloze", "contrast"}:
            continue
        header, rows = parse_tsv(path)
        if not header:
            continue
        idx = {k: i for i, k in enumerate(header)}
        for row in rows:
            tags = row[-1].split()
            points = [t[len("point:") :] for t in tags if t.startswith("point:")]
            if not points:
                continue
            fields = []
            for k in ("Formula", "Answer", "Hint", "Label", "Target", "OptionA", "OptionB", "MainUse", "QuickCue"):
                if k in idx:
                    fields.append(row[idx[k]])
            joined = " ".join(fields)
            tokens = JP_TOKEN_RE.findall(joined)
            for pt in points:
                if pt not in unresolved_points:
                    continue
                for tok in tokens:
                    token_counts[pt][tok] += 1

    candidates = []
    for u in unresolved:
        pt = u["point_slug"]
        c = token_counts.get(pt, Counter())
        opts = []
        for tok, n in c.most_common(20):
            if tok in STOP:
                continue
            if len(tok) < 2:
                continue
            if tok in bunpro_expr:
                opts.append({"bunpro_slug_or_title": tok, "evidence_count": n})
        candidates.append(
            {
                **u,
                "candidate_count": len(opts),
                "candidates": opts[:10],
            }
        )

    # Sort for triage: points with candidates first, then by candidate evidence.
    candidates.sort(
        key=lambda x: (
            0 if x["candidate_count"] > 0 else 1,
            -(x["candidates"][0]["evidence_count"] if x["candidate_count"] else 0),
            x["module"],
            x["point_slug"],
        )
    )

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "unresolved_points": len(unresolved),
        "with_candidates": sum(1 for c in candidates if c["candidate_count"] > 0),
        "without_candidates": sum(1 for c in candidates if c["candidate_count"] == 0),
        "candidates": candidates,
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Bunpro Mapping Candidates",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Unresolved points: `{payload['unresolved_points']}`",
        f"- With candidates: `{payload['with_candidates']}`",
        f"- Without candidates: `{payload['without_candidates']}`",
        "",
        "## Top Candidates",
        "",
    ]
    for c in candidates[:120]:
        if c["candidate_count"] == 0:
            lines.append(f"- `{c['point_slug']}` ({c['module']}, {c['jlpt'] or 'n?'}) -> no candidate")
            continue
        top = c["candidates"][0]
        lines.append(
            f"- `{c['point_slug']}` ({c['module']}, {c['jlpt'] or 'n?'}) "
            f"-> `{top['bunpro_slug_or_title']}` (evidence={top['evidence_count']})"
        )
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(f"wrote_json={OUT_JSON}")
    print(f"wrote_md={OUT_MD}")
    print(f"with_candidates={payload['with_candidates']}")
    print(f"without_candidates={payload['without_candidates']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
