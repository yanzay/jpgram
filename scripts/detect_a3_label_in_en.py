#!/usr/bin/env python3
"""A3 — EN-column-holds-label detector.

Scans the English-translation slot of Recognition (EN), Production (Prompt),
Dictation (EN), Listening (EN). Flags cells that look like a metadata label
rather than a full English translation.

Heuristics (a cell is flagged if it matches ANY):
  (a) length < 30 chars AND contains no spaces — strong signal it's a label.
  (b) no sentence-ending punctuation (. ! ?) AND length < 35 AND no verb-y
      function word, suggesting a noun fragment / label.
  (c) EN cell is byte-identical to MainUse (recognition) or Why (production).
  (d) cell matches ^[a-z][a-z\- ]+$ with no copula/aux verb word.

Stdlib only.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "grammar-strict"

VERB_HINTS = {
    "is", "are", "was", "were", "be", "been", "being",
    "am", "do", "does", "did",
    "have", "has", "had",
    "will", "would", "shall", "should",
    "can", "could", "may", "might", "must",
    "go", "goes", "went", "going", "gone",
    "get", "gets", "got",
    "make", "makes", "made", "making",
    "take", "takes", "took", "taken", "taking",
    "say", "said", "says", "saying",
    "see", "sees", "saw", "seen",
    "come", "comes", "came",
    "want", "wants", "wanted",
    "need", "needs",
    "let", "lets",
    "i", "you", "we", "they", "he", "she", "it",
    "my", "your", "our", "their", "his", "her",
}

LOWER_LABEL_RE = re.compile(r"^[a-z][a-z \-/]{1,30}$")


def has_sentence_punct(cell: str) -> bool:
    return any(p in cell for p in (".", "!", "?", "…"))


def has_verb_or_pronoun(cell: str) -> bool:
    words = re.findall(r"[A-Za-z']+", cell.lower())
    if any(w in VERB_HINTS for w in words):
        return True
    # -ed or -ing endings as verb hint
    for w in words:
        if len(w) > 3 and (w.endswith("ed") or w.endswith("ing") or w.endswith("'s")):
            return True
    return False


def cell_reasons(cell: str, mainuse_or_why: str = "") -> list[str]:
    reasons: list[str] = []
    s = cell.strip()
    if not s:
        return reasons  # empty handled elsewhere; not the bug class A3 targets
    if len(s) < 30 and " " not in s and re.search(r"[A-Za-z]", s):
        reasons.append("no-spaces-short")
    if not has_sentence_punct(s) and len(s) < 35 and not has_verb_or_pronoun(s):
        if re.search(r"[A-Za-z]", s):
            reasons.append("no-punct-no-verb-short")
    if mainuse_or_why and s == mainuse_or_why.strip():
        reasons.append("identical-to-mainuse-or-why")
    if LOWER_LABEL_RE.match(s) and not has_verb_or_pronoun(s):
        reasons.append("lowercase-label-pattern")
    return reasons


def detect(root: Path) -> list[dict]:
    hits: list[dict] = []
    # Recognition: EN column, with MainUse for identity check.
    for path in sorted(root.rglob("*_recognition.tsv")):
        cols = None
        with path.open("r", encoding="utf-8") as f:
            for raw in f:
                if raw.startswith("#columns:"):
                    cols = raw.rstrip("\n")[len("#columns:"):].split("\t")
                    break
        if not cols:
            continue
        try:
            en_i = cols.index("EN")
            mu_i = cols.index("MainUse")
            jp_i = cols.index("JP")
        except ValueError:
            continue
        with path.open("r", encoding="utf-8") as f:
            for lineno, raw in enumerate(f, 1):
                line = raw.rstrip("\n")
                if not line or line.startswith("#"):
                    continue
                parts = line.split("\t")
                if len(parts) <= max(en_i, mu_i):
                    continue
                en = parts[en_i]
                mu = parts[mu_i]
                rs = cell_reasons(en, mu)
                if rs:
                    hits.append({
                        "path": str(path),
                        "line": lineno,
                        "kind": "recognition.EN",
                        "jp": parts[jp_i] if len(parts) > jp_i else "",
                        "cell": en,
                        "reasons": rs,
                    })
    # Production: Prompt column is the English source; check identity vs Why
    for path in sorted(root.rglob("*_production.tsv")):
        cols = None
        with path.open("r", encoding="utf-8") as f:
            for raw in f:
                if raw.startswith("#columns:"):
                    cols = raw.rstrip("\n")[len("#columns:"):].split("\t")
                    break
        if not cols:
            continue
        try:
            pr_i = cols.index("Prompt")
            why_i = cols.index("Why")
            target_i = cols.index("Target")
        except ValueError:
            continue
        with path.open("r", encoding="utf-8") as f:
            for lineno, raw in enumerate(f, 1):
                line = raw.rstrip("\n")
                if not line or line.startswith("#"):
                    continue
                parts = line.split("\t")
                if len(parts) <= max(pr_i, why_i):
                    continue
                pr = parts[pr_i]
                why = parts[why_i]
                rs = cell_reasons(pr, why)
                if rs:
                    hits.append({
                        "path": str(path),
                        "line": lineno,
                        "kind": "production.Prompt",
                        "jp": parts[target_i] if len(parts) > target_i else "",
                        "cell": pr,
                        "reasons": rs,
                    })
    # Dictation / Listening: scan EN column if present.
    for pattern in ("*_dictation.tsv", "*_listening.tsv"):
        for path in sorted(root.rglob(pattern)):
            cols = None
            with path.open("r", encoding="utf-8") as f:
                for raw in f:
                    if raw.startswith("#columns:"):
                        cols = raw.rstrip("\n")[len("#columns:"):].split("\t")
                        break
            if not cols or "EN" not in cols:
                continue
            en_i = cols.index("EN")
            jp_i = cols.index("JP") if "JP" in cols else None
            with path.open("r", encoding="utf-8") as f:
                for lineno, raw in enumerate(f, 1):
                    line = raw.rstrip("\n")
                    if not line or line.startswith("#"):
                        continue
                    parts = line.split("\t")
                    if len(parts) <= en_i:
                        continue
                    en = parts[en_i]
                    rs = cell_reasons(en)
                    if rs:
                        hits.append({
                            "path": str(path),
                            "line": lineno,
                            "kind": Path(path).name.split("_")[-1].replace(".tsv", "") + ".EN",
                            "jp": parts[jp_i] if jp_i is not None and len(parts) > jp_i else "",
                            "cell": en,
                            "reasons": rs,
                        })
    return hits


def main() -> int:
    hits = detect(ROOT)
    print(f"# A3 hits: {len(hits)}")
    for h in hits:
        print(f"{h['path']}:{h['line']}\t{h['kind']}\treasons={','.join(h['reasons'])}\tcell={h['cell']}\tJP={h['jp']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
