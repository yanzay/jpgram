#!/usr/bin/env bash
# release.sh — build and draft a new GitHub release after a content wave.
#
# Usage:
#   ./scripts/release.sh [patch|minor|major]   # default: patch
#
# What it does:
#   1. Validates all grammar data (fast local check).
#   2. Bumps VERSION in build_anki_package.py.
#   3. Builds japanese_grammar_anki.apkg with local audio.
#   4. Updates CHANGELOG.md header with the new version + today's date.
#   5. Commits the version bump + rebuilt apkg.
#   6. Tags the commit (vX.Y.Z) and pushes tag + commit to origin/main.
#   7. Creates a draft GitHub release with the .apkg attached.
#      → CI runs validators on the tag; on success it publishes the draft.
#
# Requirements: gh CLI authenticated, python3, git on PATH.

set -euo pipefail
cd "$(dirname "$0")/.."

BUMP="${1:-patch}"

# ── 1. Quick local validation ────────────────────────────────────────────
echo "==> Validating grammar data..."
python3 validate_anki_data.py
python3 validate_grammar_taxonomy.py
python3 scripts/strict_deck_audit.py --skip-bunpro-fetch --require-full-bunpro-resolution
echo "    Validation passed."

# ── 2. Bump version ──────────────────────────────────────────────────────
CURRENT=$(grep '^VERSION' build_anki_package.py | sed 's/VERSION = "\(.*\)"/\1/')
IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT"
case "$BUMP" in
  major) MAJOR=$((MAJOR+1)); MINOR=0; PATCH=0 ;;
  minor) MINOR=$((MINOR+1)); PATCH=0 ;;
  patch) PATCH=$((PATCH+1)) ;;
  *)     echo "Unknown bump type: $BUMP  (use patch|minor|major)"; exit 1 ;;
esac
NEW_VERSION="${MAJOR}.${MINOR}.${PATCH}"
TAG="v${NEW_VERSION}"

echo "==> Bumping version: ${CURRENT} → ${NEW_VERSION}"
sed -i '' "s/^VERSION = \"${CURRENT}\"/VERSION = \"${NEW_VERSION}\"/" build_anki_package.py

# ── 3. Build .apkg ───────────────────────────────────────────────────────
# --exclude-broken suppresses cloze/dictation/listening files until the
# Phase-2/3/8 re-curation lands (see IMPROVEMENT_PLAN.md). Refine to a
# per-file allowlist once cleanups complete.
echo "==> Building japanese_grammar_anki.apkg..."
python3 build_anki_package.py --exclude-broken
echo "    Build complete: $(du -sh japanese_grammar_anki.apkg | cut -f1)"

# ── 4. Commit ────────────────────────────────────────────────────────────
echo "==> Committing version bump and rebuilt package..."
git add build_anki_package.py japanese_grammar_anki.apkg
git commit -m "Release ${TAG}"

# ── 5. Tag and push ──────────────────────────────────────────────────────
echo "==> Tagging ${TAG} and pushing..."
git tag "${TAG}"
git push origin main "${TAG}"

# ── 6. Draft GitHub release ──────────────────────────────────────────────
echo "==> Creating draft release ${TAG}..."
gh release create "${TAG}" \
  --title "${TAG}" \
  --generate-notes \
  --draft \
  japanese_grammar_anki.apkg

echo ""
echo "Done. Draft release ${TAG} created with japanese_grammar_anki.apkg."
echo "CI is now running validators. The draft will be published automatically"
echo "once all checks pass (see Actions tab)."
echo ""
echo "To publish manually:  gh release edit ${TAG} --draft=false"
