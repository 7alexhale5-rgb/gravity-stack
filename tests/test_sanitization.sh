#!/usr/bin/env bash
# Sanitization test: fails if any tracked/untracked-but-not-ignored file leaks
# references covered by the configured patterns. CI runs the generic profile;
# maintainers must also run the external private profile before publishing.
#
# Scopes to `git ls-files` so node_modules, .next, and other gitignored paths
# are naturally excluded. Portable across macOS and Linux xargs.

set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PATTERNS_FILE="$ROOT/tests/sanitization-patterns.txt"
FAILED=0

if [ ! -f "$PATTERNS_FILE" ]; then
  echo "sanitization: missing $PATTERNS_FILE"
  exit 2
fi

# Client and project codenames are maintainer-only: they live in a file kept
# OUTSIDE this repo, named by GRAVITY_PRIVATE_PATTERNS (same idea as repo A's
# DEVPROTO_PRIVATE_PATTERNS), never in the tracked sanitization-patterns.txt.
PATTERNS_FILES=("$PATTERNS_FILE")
if [ -n "${GRAVITY_PRIVATE_PATTERNS:-}" ]; then
  if [ -f "$GRAVITY_PRIVATE_PATTERNS" ] && [ -r "$GRAVITY_PRIVATE_PATTERNS" ]; then
    # Resolve against the caller's directory before switching to the repo root.
    private_dir="$(cd -- "$(dirname -- "$GRAVITY_PRIVATE_PATTERNS")" && pwd)" || exit 2
    PATTERNS_FILES+=("$private_dir/$(basename -- "$GRAVITY_PRIVATE_PATTERNS")")
  else
    echo "sanitization: GRAVITY_PRIVATE_PATTERNS set but not found: $GRAVITY_PRIVATE_PATTERNS"
    exit 2
  fi
fi

cd "$ROOT" || exit 2

# Stream: tracked files + newly-added unignored files; skip self + binaries
FILE_LIST=$(git ls-files --cached --others --exclude-standard 2>/dev/null \
  | grep -vE '^tests/(test_sanitization\.sh|sanitization-patterns\.txt)$' \
  | grep -vE '\.(png|jpg|jpeg|gif|mp4|woff2?|ttf|otf|ico|lock)$' \
  || true)

if [ -z "$FILE_LIST" ]; then
  echo "sanitization: no files to scan"
  exit 0
fi

PATTERN_NUMBER=0
for pf in "${PATTERNS_FILES[@]}"; do
  while IFS= read -r pattern || [ -n "$pattern" ]; do
    [ -z "$pattern" ] && continue
    [[ "$pattern" =~ ^# ]] && continue

    PATTERN_NUMBER=$((PATTERN_NUMBER+1))
    grep -E -- "$pattern" /dev/null >/dev/null 2>&1
    regex_status=$?
    if [ "$regex_status" -gt 1 ]; then
      echo "sanitization: invalid pattern at index $PATTERN_NUMBER"
      exit 2
    fi
    HITS=$(echo "$FILE_LIST" | xargs -I {} grep -IlE -- "$pattern" {} 2>/dev/null || true)
    if [ -n "$HITS" ]; then
      echo "LEAK: pattern index $PATTERN_NUMBER found in:"
      echo "$HITS" | sort -u | sed 's|^|  |'
      FAILED=$((FAILED+1))
    fi
  done < "$pf"
done

if [ "$FAILED" -eq 0 ]; then
  echo "sanitization: clean"
  exit 0
fi

echo ""
echo "sanitization: FAILED ($FAILED leaks)"
exit 1
