# `draft/` — example TSVs (NOT shipped in the deck)

This directory holds **schema-only example TSVs**, one per note type,
showing the `#columns:` header and one well-formed sample row.

These files are intentionally **outside `grammar/`** so the build
pipeline never picks them up. They contain placeholder audio refs
(`[sound:WAVE0_PLACEHOLDER.mp3]`) — the validator will reject any TSV
under `grammar/` that contains the same placeholder.

| File | Note type | Schema (from `build_anki_package.NOTE_TYPES`) |
|---|---|---|
| `example_recognition.tsv` | Recognition | `JP · Reading · EN · Label · Formula · MainUse · QuickCue · Contrast · Audio · Tags` |
| `example_production.tsv`  | Production  | `Prompt · Target · Reading · Sample · Why · Audio · Tags` |
| `example_cloze.tsv`       | Cloze       | `Text · Reading · Hint · Audio · Tags` (Text must contain `{{c1::…}}`) |
| `example_contrast.tsv`    | Contrast    | `JP · OptionA · OptionB · Answer · Why · Tip · Audio · Tags` |

To author a new TSV: copy the matching example into the appropriate
`grammar/<module>/` subdirectory, rename it
`<point-slug>_<notetype>.tsv`, replace the example row(s) with real
content, then `python apply_taxonomy_tags.py` and
`python validate_anki_data.py`.
