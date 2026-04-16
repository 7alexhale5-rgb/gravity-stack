#!/bin/bash
# PreToolUse hook for Bash commands — blocks dangerous operations
# Exit 0 with JSON deny = block | Exit 0 with no output = allow

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

if [ -z "$COMMAND" ]; then
  exit 0
fi

# Destructive filesystem ops — rm -rf on sensitive paths
if echo "$COMMAND" | grep -qE 'rm\s+-r[f]?\s+(/|~|\$HOME|\.\.|/Users)'; then
  jq -n '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:"BLOCKED: recursive delete on sensitive path. Target specific files instead."}}'
  exit 0
fi

# Force push to main/master (even with --force-with-lease)
if echo "$COMMAND" | grep -qE 'git\s+push\s+.*--force.*\s+(main|master)($|\s)'; then
  jq -n '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:"BLOCKED: force push to main/master. This is almost never what you want."}}'
  exit 0
fi

# Force push without --force-with-lease (on non-main branches)
if echo "$COMMAND" | grep -qE 'git\s+push\s+.*--force($|\s)' && ! echo "$COMMAND" | grep -qE '--force-with-lease'; then
  jq -n '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:"BLOCKED: git push --force. Use --force-with-lease for safer overwrites."}}'
  exit 0
fi

# Database destruction
if echo "$COMMAND" | grep -qiE 'DROP\s+(TABLE|DATABASE|SCHEMA)'; then
  jq -n '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:"BLOCKED: DROP statement detected. Use migrations for schema changes."}}'
  exit 0
fi

# git reset --hard
if echo "$COMMAND" | grep -qE 'git\s+reset\s+--hard'; then
  jq -n '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:"BLOCKED: git reset --hard discards uncommitted work. Stash or commit first."}}'
  exit 0
fi

# git clean -f (force delete untracked files)
if echo "$COMMAND" | grep -qE 'git\s+clean\s+-[a-zA-Z]*f'; then
  jq -n '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:"BLOCKED: git clean -f deletes untracked files permanently. Review with git clean -n first."}}'
  exit 0
fi

# Credential exposure via pipe
if echo "$COMMAND" | grep -qE 'echo.*(_KEY|_SECRET|_TOKEN|PASSWORD).*\|'; then
  jq -n '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:"BLOCKED: potential credential exposure via pipe. Use env vars directly."}}'
  exit 0
fi

exit 0
