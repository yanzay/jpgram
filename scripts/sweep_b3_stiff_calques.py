#!/usr/bin/env python3
"""Phase 7.5 sweep B3 — N1/N2 stiff calque translations.

Each rule pairs a JP form with a stiff EN signature. ずにはいられない /
"cannot help but" is excluded (acceptable rendering).
"""
from __future__ import annotations

import re
import sys
from typing import List, Tuple

sys.path.insert(0, "/Users/ograc/projects/jpgram/scripts")
from _sweep_common import iter_card_files, get_jp_en_pairs, CARD_SUFFIXES

# (rule_id, jp_pattern, en_pattern, severity)
RULES = [
    (
        "premise",
        re.compile(r"を前提に|を前提とした|を前提として"),
        re.compile(
            r"as\s+the\s+premise|with\s+\S+\s+as\s+the\s+premise|presupposing\s+as",
            re.IGNORECASE,
        ),
        "HIGH",
    ),
    (
        "ataru",
        re.compile(r"に当たる|に当たって|に当たり"),
        re.compile(r"corresponds\s+to|is\s+equivalent\s+to", re.IGNORECASE),
        "HIGH",
    ),
    (
        "kotoninaru",
        re.compile(r"ことになる|ことになりました|ことになった"),
        re.compile(
            r"it\s+has\s+come\s+about|it\s+has\s+been\s+decided\s+that|has\s+come\s+to\s+be\s+the\s+case",
            re.IGNORECASE,
        ),
        "HIGH",
    ),
    (
        "wokini",
        re.compile(r"を機に|を契機に|を契機として"),
        re.compile(
            r"using\s+\S+\s+as\s+an?\s+opportunity|taking\s+\S+\s+as\s+(?:an\s+)?opportunity|with\s+\S+\s+as\s+the\s+opportunity",
            re.IGNORECASE,
        ),
        "HIGH",
    ),
    (
        "hokanaranai",
        re.compile(r"に他ならない|にほかならない"),
        re.compile(r"is\s+none\s+other\s+than", re.IGNORECASE),
        "HIGH",
    ),
    (
        "yoginaku",
        re.compile(r"を余儀なくされ"),
        re.compile(
            r"was\s+forced\s+into\s+the\s+situation\s+of|were\s+forced\s+into\s+the\s+situation\s+of",
            re.IGNORECASE,
        ),
        "HIGH",
    ),
]


def main() -> int:
    findings: List[Tuple[str, str, int, str, str, str, str]] = []
    per_rule_total = {rid: 0 for rid, *_ in RULES}
    per_rule_hits = {rid: 0 for rid, *_ in RULES}

    for path in iter_card_files(CARD_SUFFIXES):
        for ln, jp, en, kind in get_jp_en_pairs(path):
            for rid, jp_pat, en_pat, sev in RULES:
                if jp_pat.search(jp):
                    per_rule_total[rid] += 1
                    if en_pat.search(en):
                        per_rule_hits[rid] += 1
                        findings.append((sev, path, ln, kind, jp, en, rid))

    findings.sort(key=lambda x: (x[6], x[1], x[2]))
    print("# B3 sweep — stiff calques")
    for rid in per_rule_total:
        print(f"# rule={rid} jp_matches={per_rule_total[rid]} stiff_en_hits={per_rule_hits[rid]}")
    print(f"# HIGH findings: {len(findings)}")
    print()
    for sev, path, ln, kind, jp, en, rid in findings:
        print(f"{sev}\t{path}\t{ln}\t{kind}\t{rid}\t{jp}\t{en}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
