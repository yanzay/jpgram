#!/usr/bin/env python3
"""
Phase-9+ Production: re-author Production files paired with the 37
Recognition files re-authored in commit 27ba639.

For each slug:
- Reuse the 5 Recognition JP sentences as Production Sample
- Reuse the Recognition Reading column
- Prompt = the English translation (already drafted in Recognition EN)
- Target = a short grammar-form cue (slug or its conjugated form on
  the row's verb), used as a self-test prompt before revealing Sample
- Why = the per-row MainUse fragment from Recognition (Phase-4 bridge)

Production schema: Prompt\tTarget\tReading\tSample\tWhy\tAudio\tTags
Audio is empty + scaffold:pending-audio.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from _phase9plus_reauthor import CONTENT as REC_CONTENT  # noqa


def make_production_tsv(entry):
    """Derive a Production TSV from a Recognition entry."""
    deck_map = {"n5": "01 - N5", "n4": "02 - N4", "n3": "03 - N3",
                "n2": "04 - N2", "n1": "05 - N1"}
    deck = f"Japanese Grammar::{deck_map[entry['jlpt']]} Grammar::Production"
    header = (
        "#separator:tab\n"
        "#html:true\n"
        "#columns:Prompt\tTarget\tReading\tSample\tWhy\tAudio\tTags\n"
        "#notetype:Production\n"
        f"#deck:{deck}\n"
        "\n"
    )
    body = []
    for jp, reading, en, mainuse, _quickcue in entry["rows"]:
        # Target: the grammar slug as a hint about what form to produce
        target = entry["slug"]
        # Why: use the per-row MainUse fragment, condensed
        why = mainuse
        tags = (
            f"module:{entry['module']} "
            f"jlpt:{entry['jlpt']} "
            f"point:{entry['slug']} "
            f"complexity:standard "
            f"source:authored "
            f"frequency:top10k "
            f"scaffold:pending-audio"
        )
        body.append(
            f"{en}\t{target}\t{reading}\t{jp}\t{why}\t\t{tags}\n"
        )
    return header + "".join(body)


def main():
    for entry in REC_CONTENT:
        rec_path = Path(entry["path"])
        # Derive production path
        prod_path = rec_path.with_name(rec_path.name.replace("_recognition", "_production"))
        if not prod_path.exists():
            print(f"  SKIP {prod_path}  (no sibling)")
            continue
        prod_path.write_text(make_production_tsv(entry), encoding="utf-8")
        print(f"  WROTE {prod_path.name}  ({len(entry['rows'])} rows)")
    print(f"\nTotal: {len(REC_CONTENT)} production files re-authored.")


if __name__ == "__main__":
    main()
