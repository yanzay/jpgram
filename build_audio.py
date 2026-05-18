#!/usr/bin/env python3
"""
Tier-2 audio builder for the Japanese Grammar Anki package.

Generates one MP3 per unique Japanese sentence appearing in the corpus
TSVs under ./grammar/ (one TSV per JLPT level / module).

Output:
  media/audio/<sha1[:12]>.mp3       — natural-rate native voice
  media/audio_manifest.json         — per-hash record of synthesis params + file fingerprint

Backend: Google Cloud Text-to-Speech, Neural2/Wavenet/Chirp3 voices.
Auth: gcloud auth application-default login
      (or GOOGLE_APPLICATION_CREDENTIALS=.secrets/gcp-adc.json)

Idempotent + incremental — see header comment in `verbs/build_audio.py`
for the full semantics. Same logic, but the corpus extractor is
specialized to Japanese-grammar TSVs.

Sentence-source columns in our schema:
  grammar/N5/*.tsv   field 0 = JP sentence
  grammar/N4/*.tsv   field 0 = JP sentence
  grammar/N3/*.tsv   field 0 = JP sentence
  grammar/N2/*.tsv   field 0 = JP sentence
  grammar/N1/*.tsv   field 0 = JP sentence
  grammar/casual/*.tsv      field 0 = JP sentence
  grammar/slang/*.tsv       field 0 = JP sentence
  grammar/keigo/*.tsv       field 0 = JP sentence
  grammar/cloze/*.tsv       field 0 = JP cloze (we strip {{c1::…}})

Cost note: at ~16 USD / 1 M chars Neural2, the full target corpus
(~12,000 sentences × ~25 JP chars ≈ 300 K chars) costs roughly
4.80 USD per full re-render. Always test with --limit first.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# ── Tunables (env or CLI) ────────────────────────────────────────────────
# JP voices: Neural2 line is the warmest. -B/-D = female, -C/-A = male.
DEFAULT_VOICE        = os.environ.get("JPG_TTS_VOICE", "ja-JP-Neural2-B")  # warm female
DEFAULT_VOICE_ALT    = os.environ.get("JPG_TTS_VOICE_ALT", "ja-JP-Neural2-C")  # male
DEFAULT_LANG         = os.environ.get("JPG_TTS_LANG", "ja-JP")
DEFAULT_RATE         = 1.00
DEFAULT_AUDIO_ENC    = "MP3"

# Optional alt-voice mode renders each sentence in a 2nd voice for
# variety. Filename convention:
#   <sha1[:12]>.mp3        primary voice
#   <sha1[:12]>_alt.mp3    alt voice (only if --alt-voice is set)

# Auto-load local creds if present and env not already set.
_LOCAL_CREDS = Path(".secrets/gcp-adc.json")
if _LOCAL_CREDS.exists() and not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(_LOCAL_CREDS.resolve())

DRY_RUN = bool(os.environ.get("JPG_TTS_DRY_RUN", "").strip())

MEDIA_DIR      = Path("media/audio")
MANIFEST_PATH  = Path("media/audio_manifest.json")
GRAMMAR_DIR    = Path("grammar-strict")

MANIFEST_VERSION = 1


# ── Google client (lazy) ─────────────────────────────────────────────────
_CLIENT = None


def _client():
    global _CLIENT
    if _CLIENT is not None:
        return _CLIENT
    try:
        from google.cloud import texttospeech as tts  # type: ignore
    except ImportError as e:
        raise SystemExit(
            "Audio builder requires `google-cloud-texttospeech`.\n"
            "  pip install google-cloud-texttospeech\n"
            "and authenticate with `gcloud auth application-default login` "
            "or place a service-account JSON at .secrets/gcp-adc.json."
        ) from e
    _CLIENT = tts.TextToSpeechClient()
    return _CLIENT


def _audio_encoding():
    from google.cloud import texttospeech as tts  # type: ignore
    return getattr(tts.AudioEncoding, DEFAULT_AUDIO_ENC)


# ── Hashing helpers ──────────────────────────────────────────────────────
def text_hash(text: str) -> str:
    """Stable 12-char id for a sentence; used as the MP3 filename stem."""
    return hashlib.sha1(text.strip().encode("utf-8")).hexdigest()[:12]


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ── Synthesis ────────────────────────────────────────────────────────────
def synth_mp3(text: str, out_path: Path, *,
              rate: float, voice_name: str, language_code: str) -> bool:
    """Render one sentence to MP3. Returns True if a file was written."""
    if DRY_RUN:
        print(f"  [dry-run] would synth {voice_name} @{rate} → {out_path.name}: {text[:60]}…")
        return False
    from google.cloud import texttospeech as tts  # type: ignore
    client = _client()
    input_ = tts.SynthesisInput(text=text)
    voice = tts.VoiceSelectionParams(language_code=language_code, name=voice_name)
    audio_config = tts.AudioConfig(
        audio_encoding=_audio_encoding(),
        speaking_rate=float(rate),
    )
    response = client.synthesize_speech(
        input=input_, voice=voice, audio_config=audio_config,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(response.audio_content)
    return True


# ── Corpus extraction ────────────────────────────────────────────────────
def load_tsv(path: Path):
    """Yield data rows (skipping #-comment lines and the #columns: header)."""
    data_lines = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        data_lines.append(line)
    reader = csv.reader(data_lines, delimiter="\t", quotechar='"')
    for row in reader:
        yield row


_CLOZE_RE = re.compile(r"\{\{c\d+::([^:}]+)(?:::[^}]+)?\}\}")
_JP_CHAR_RE = re.compile(r"[一-龯ぁ-んァ-ン]")


def collect_sentences() -> List[str]:
    """Return a sorted list of unique Japanese sentences across all corpus TSVs.

    Convention (see grammar/README.md):
      * column 0 of every grammar TSV = the Japanese sentence learners hear.
      * cloze TSVs use Anki's {{c1::…}} markup which we strip before TTS.
      * contrast TSVs (`*_contrast.tsv`) have `___` placeholders; we substitute
        the Answer column to produce the JP sentence that's actually synthesized.
      * production TSVs (`*_production.tsv`) hash the Sample column, not Prompt.
    """
    sentences = set()
    if not GRAMMAR_DIR.exists():
        return []
    for tsv in sorted(GRAMMAR_DIR.rglob("*.tsv")):
        is_cloze    = "cloze"    in tsv.stem.lower()
        is_contrast = "contrast" in tsv.stem.lower()
        is_prod     = "production" in tsv.stem.lower()
        # Find the header so we can index into Answer / Sample columns.
        header = None
        for raw in tsv.read_text(encoding="utf-8").splitlines():
            if raw.startswith("#columns:"):
                header = raw[len("#columns:"):].split("\t")
                break
        for row in load_tsv(tsv):
            if not row:
                continue
            # Pick the source column to synthesize from.
            if is_prod and header and "Sample" in header and "Target" in header:
                sample_idx = header.index("Sample")
                target_idx = header.index("Target")
                sample = row[sample_idx].strip() if len(row) > sample_idx else ""
                target = row[target_idx].strip() if len(row) > target_idx else ""
                # Some production rows mistakenly contain English in Sample.
                # Prefer Sample when it is Japanese; otherwise fall back to Target.
                jp = sample if sample and _JP_CHAR_RE.search(sample) else (target or sample)
            else:
                jp = row[0].strip()
            if not jp:
                continue
            if is_cloze:
                jp = _CLOZE_RE.sub(r"\1", jp)
            if is_contrast and header and "Answer" in header and len(row) > header.index("Answer"):
                ans = row[header.index("Answer")].strip()
                jp = jp.replace("___", ans)
            sentences.add(jp)
    return sorted(sentences)


# ── Manifest I/O ─────────────────────────────────────────────────────────
def load_manifest() -> dict:
    if MANIFEST_PATH.exists():
        try:
            data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
            if data.get("version") == MANIFEST_VERSION and "entries" in data:
                return data
        except json.JSONDecodeError:
            pass
    return {"version": MANIFEST_VERSION, "entries": {}}


def save_manifest(manifest: dict) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    manifest["entries"] = dict(sorted(manifest["entries"].items()))
    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def manifest_entry(text: str, *, voice: str, rate: float, lang: str,
                   mp3_path: Path) -> dict:
    return {
        "text": text,
        "voice": voice,
        "rate": round(float(rate), 4),
        "lang": lang,
        "sha256": file_sha256(mp3_path) if mp3_path.exists() and mp3_path.stat().st_size > 0 else "",
        "size": mp3_path.stat().st_size if mp3_path.exists() else 0,
    }


def entry_matches(entry: dict, *, text: str, voice: str, rate: float, lang: str,
                  mp3_path: Path, verify_sha: bool) -> Tuple[bool, str]:
    if not mp3_path.exists():
        return False, "missing-file"
    if mp3_path.stat().st_size == 0:
        return False, "zero-byte-file"
    if entry.get("text") != text:
        return False, "text-changed"
    if entry.get("voice") != voice:
        return False, "voice-changed"
    if round(float(entry.get("rate", 0)), 4) != round(float(rate), 4):
        return False, "rate-changed"
    if entry.get("lang") != lang:
        return False, "lang-changed"
    if verify_sha:
        recorded = entry.get("sha256", "")
        if not recorded:
            return False, "no-recorded-sha"
        if file_sha256(mp3_path) != recorded:
            return False, "sha-mismatch"
    return True, "ok"


# ── Driver ───────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description="JP-grammar audio builder (idempotent + incremental)")
    ap.add_argument("--voice", default=DEFAULT_VOICE,
                    help="Google TTS voice name (default: ja-JP-Neural2-B)")
    ap.add_argument("--lang", default=DEFAULT_LANG,
                    help="BCP-47 language code (default ja-JP)")
    ap.add_argument("--rate", type=float, default=DEFAULT_RATE,
                    help="Speech rate (default 1.00)")
    ap.add_argument("--limit", type=int, default=0,
                    help="Limit to first N sentences (0 = all). Cost-control for smoke runs. "
                         "When set, prune is automatically disabled.")
    ap.add_argument("--force", action="store_true",
                    help="Re-render every MP3 even if params + sha already match")
    ap.add_argument("--no-prune", action="store_true",
                    help="Keep MP3s whose sentence is no longer in the corpus")
    ap.add_argument("--no-verify-sha", action="store_true",
                    help="Skip sha256 verification of existing MP3s (faster on huge corpora)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Don't call the API and don't modify files; show what WOULD change")
    ap.add_argument("--rehash", action="store_true",
                    help="Recompute manifest sha256/size for all on-disk MP3s without re-synthesizing.")
    ap.add_argument("--alt-voice", default="",
                    help=f"Also render each sentence with this voice as "
                         f"<hash>_alt.mp3 (e.g. {DEFAULT_VOICE_ALT}). Empty = off.")
    args = ap.parse_args()

    if args.dry_run:
        global DRY_RUN
        DRY_RUN = True

    full_sentences = collect_sentences()
    sentences = full_sentences[:args.limit] if args.limit else full_sentences

    manifest = load_manifest()
    entries: Dict[str, dict] = manifest["entries"]

    # ── Rehash mode ──
    if args.rehash:
        print("Rehash mode: rebuilding manifest from on-disk MP3s (no synthesis).")
        text_by_hash = {text_hash(s): s for s in full_sentences}
        rebuilt = 0
        for mp3 in sorted(MEDIA_DIR.glob("*.mp3")):
            h = mp3.stem
            text = text_by_hash.get(h, entries.get(h, {}).get("text", ""))
            entries[h] = {
                "text": text,
                "voice": args.voice,
                "rate": round(float(args.rate), 4),
                "lang": args.lang,
                "sha256": file_sha256(mp3),
                "size": mp3.stat().st_size,
            }
            rebuilt += 1
        if not DRY_RUN:
            save_manifest(manifest)
        print(f"  Rehashed {rebuilt} entries → {MANIFEST_PATH}")
        return

    print(f"Corpus: {len(sentences)} unique JP sentences "
          f"(voice={args.voice} lang={args.lang} rate={args.rate}).")

    written = up_to_date = stale = missing = 0
    reasons: Dict[str, int] = {}

    for i, text in enumerate(sentences, 1):
        h = text_hash(text)
        out = MEDIA_DIR / f"{h}.mp3"
        existing = entries.get(h)

        need = True
        reason = "new"
        if not args.force and existing is not None and out.exists():
            ok, why = entry_matches(existing,
                                    text=text, voice=args.voice,
                                    rate=args.rate, lang=args.lang,
                                    mp3_path=out,
                                    verify_sha=not args.no_verify_sha)
            if ok:
                need = False
            else:
                reason = why
        elif not out.exists():
            reason = "missing-file"
        elif args.force:
            reason = "force"

        if need:
            reasons[reason] = reasons.get(reason, 0) + 1
            if reason == "missing-file":
                missing += 1
            elif reason != "new":
                stale += 1
            wrote = synth_mp3(text, out,
                              rate=args.rate, voice_name=args.voice,
                              language_code=args.lang)
            if wrote:
                written += 1
                entries[h] = manifest_entry(text,
                                            voice=args.voice, rate=args.rate,
                                            lang=args.lang, mp3_path=out)
            # ── Optional alt-voice variant ──
            if args.alt_voice:
                alt_out = MEDIA_DIR / f"{h}_alt.mp3"
                if args.force or not alt_out.exists():
                    if synth_mp3(text, alt_out, rate=args.rate,
                                 voice_name=args.alt_voice,
                                 language_code=args.lang):
                        entries.setdefault(h, {}).setdefault(
                            "alt", manifest_entry(text, voice=args.alt_voice,
                                                  rate=args.rate, lang=args.lang,
                                                  mp3_path=alt_out))
        else:
            up_to_date += 1
            if existing is None or "sha256" not in existing or not existing.get("sha256"):
                entries[h] = manifest_entry(text,
                                            voice=args.voice, rate=args.rate,
                                            lang=args.lang, mp3_path=out)

        if i % 100 == 0 or i == len(sentences):
            print(f"  [{i}/{len(sentences)}] written={written} "
                  f"up-to-date={up_to_date} stale-rerendered={stale} "
                  f"missing-rendered={missing}")

    # ── Prune orphans ──
    desired = {text_hash(s) for s in full_sentences}
    pruned = 0
    if args.limit and not args.no_prune:
        if not DRY_RUN:
            print("  (prune skipped because --limit was used; run without --limit to prune)")
        args.no_prune = True
    if not args.no_prune and MEDIA_DIR.exists():
        for mp3 in sorted(MEDIA_DIR.glob("*.mp3")):
            if mp3.stem not in desired:
                if DRY_RUN:
                    print(f"  [dry-run] would prune orphan audio/{mp3.name}")
                else:
                    mp3.unlink()
                pruned += 1
                entries.pop(mp3.stem, None)

    if not DRY_RUN:
        save_manifest(manifest)

    print(f"\n✓ Done. written={written}  up-to-date={up_to_date}  pruned={pruned}")
    if reasons:
        details = ", ".join(f"{k}={v}" for k, v in sorted(reasons.items()))
        print(f"  re-render reasons: {details}")
    print(f"  Manifest: {MANIFEST_PATH}")
    print(f"  Output dir: {MEDIA_DIR}/")


if __name__ == "__main__":
    main()
