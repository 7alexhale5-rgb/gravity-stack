#!/bin/bash
# ~/.claude/hooks/log-event.sh <event-name>
# Unified logger for Wave 1 hook events.
# Invoked by settings.json hooks.{PermissionDenied,StopFailure,CwdChanged,FileChanged,TaskCreated}.
# Reads tool_use JSON from stdin, extracts salient fields, appends to ~/Assets/logs/cc-events.log.
#
# Security posture (post-/review-stack --audit hardening 2026-04-15):
# - F1: osascript called via heredoc + `system attribute` — payload never crosses shell→AppleScript
#   parser as a string literal, eliminating AppleScript escape-ladder injection.
# - F2: umask 077 + chmod 600 on log file. Secret-path file_paths redacted to `<redacted>`.
# - F3: DETAIL sanitized of CR/LF/NUL before logging, one-line invariant enforced.

set -u
EVENT="${1:-unknown}"
LOG_DIR="$HOME/Assets/logs"
LOG_FILE="$LOG_DIR/cc-events.log"

# F2: restrict log file to user only.
umask 077
mkdir -p "$LOG_DIR" 2>/dev/null || exit 0
if [ ! -f "$LOG_FILE" ]; then
  : > "$LOG_FILE"
  chmod 600 "$LOG_FILE" 2>/dev/null || true
fi

TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
INPUT=$(cat 2>/dev/null || true)

if [ -z "$INPUT" ]; then
  echo "$TS [$EVENT] (no-stdin)" >> "$LOG_FILE"
  exit 0
fi

# Python filter: keep only known-safe fields, redact secret-bearing paths, hard-cap at 500 chars.
DETAIL=$(printf '%s' "$INPUT" | python3 -c "
import json, sys
SECRET_MARKERS = ('.env', 'credentials', '.pem', 'id_rsa', '.ssh/', '.claude.json', 'secrets/')
KEEP = ('tool_name','cwd','new_cwd','old_cwd','file_path','file_paths','error','reason','sub_matcher','task_id','subagent_type','description')
try:
    d = json.load(sys.stdin)
    for k in ('file_path',):
        v = d.get(k)
        if isinstance(v, str) and any(s in v for s in SECRET_MARKERS):
            d[k] = '<redacted>'
    keep = {k: v for k, v in d.items() if k in KEEP}
    print(json.dumps(keep, default=str)[:500])
except Exception:
    print('{}')
" 2>/dev/null)

# F4 (cq3): decouple from python pipeline-|| fragility.
[ -z "$DETAIL" ] && DETAIL='{}'

# F3: strip control chars so a malicious \r\n in a field can't forge log entries.
DETAIL=$(printf '%s' "$DETAIL" | tr -d '\r\n\0')

echo "$TS [$EVENT] $DETAIL" >> "$LOG_FILE"

# F1 fix: pass payload via env + `system attribute`. AppleScript reads env var as inert data —
# no string-literal re-parsing, no escape-ladder injection, no RCE primitive.
case "$EVENT" in
  FileChanged)
    export CC_HOOK_DETAIL="$DETAIL"
    export CC_HOOK_TITLE="CC FileChanged"
    /usr/bin/osascript <<'APPLESCRIPT' 2>/dev/null || true
set d to (system attribute "CC_HOOK_DETAIL")
set t to (system attribute "CC_HOOK_TITLE")
display notification ("Watched file changed: " & d) with title t sound name "Funk"
APPLESCRIPT
    ;;
  StopFailure)
    if printf '%s' "$DETAIL" | grep -qE "billing|authentication|rate_limit"; then
      export CC_HOOK_DETAIL="$DETAIL"
      export CC_HOOK_TITLE="CC StopFailure"
      /usr/bin/osascript <<'APPLESCRIPT' 2>/dev/null || true
set d to (system attribute "CC_HOOK_DETAIL")
set t to (system attribute "CC_HOOK_TITLE")
display notification ("Stop failure: " & d) with title t sound name "Basso"
APPLESCRIPT
    fi
    ;;
esac

exit 0
