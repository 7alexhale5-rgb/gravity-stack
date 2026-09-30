#!/usr/bin/env bash
# Sanitization test: fails if any tracked/untracked-but-not-ignored file leaks
# personal or proprietary references. Run before commit. CI-enforced.
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
  if [ -f "$GRAVITY_PRIVATE_PATTERNS" ]; then
    PATTERNS_FILES+=("$GRAVITY_PRIVATE_PATTERNS")
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

for pf in "${PATTERNS_FILES[@]}"; do
  while IFS= read -r pattern; do
    [ -z "$pattern" ] && continue
    [[ "$pattern" =~ ^# ]] && continue

    HITS=$(echo "$FILE_LIST" | xargs -I {} grep -IlE "$pattern" {} 2>/dev/null || true)
    if [ -n "$HITS" ]; then
      echo "LEAK: pattern '$pattern' found in:"
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
