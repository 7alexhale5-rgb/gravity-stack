export interface Hook {
  name: string;
  event: "Notification" | "PreCompact" | "PreToolUse" | "PostToolUse" | "SessionStart" | "UserPromptSubmit";
  matcher?: string;
  description: string;
  why: string;
  code: string;
  language: "bash" | "python";
}

export const hooks: Hook[] = [
  {
    name: "Notification",
    event: "Notification",
    description: "Sends a macOS notification when Claude needs human input and the terminal is in the background.",
    why: "You're working in another app. Claude finishes a task and needs approval. This pings you with a macOS notification so you don't leave it waiting.",
    code: `osascript -e 'display notification "Claude needs input" with title "Claude Code" sound name "Ping"'`,
    language: "bash",
  },
  {
    name: "Session Backup",
    event: "PreCompact",
    description: "Saves the full session transcript before context compaction.",
    why: "Context compaction is lossy. This saves the full session transcript before compression, so you never lose work.",
    code: `mkdir -p ~/.claude/backups && \\
cp ~/.claude/current-session.jsonl \\
   ~/.claude/backups/session-$(date +%Y%m%d-%H%M%S).jsonl`,
    language: "bash",
  },
  {
    name: "File Guard",
    event: "PreToolUse",
    matcher: "Edit|Write",
    description: "Prevents Claude from modifying sensitive files without explicit approval.",
    why: "Prevents Claude from modifying sensitive files (secrets, lockfiles, git internals, database migrations) without explicit approval. Exit code 2 = block the action.",
    code: `import json, sys
data = json.load(sys.stdin)
path = data.get('tool_input', {}).get('file_path', '')
GUARDED = ['.env', 'package-lock.json', '.git/', 'supabase/migrations/']
sys.exit(2 if any(p in path for p in GUARDED) else 0)`,
    language: "python",
  },
  {
    name: "Commit Gate",
    event: "PreToolUse",
    matcher: "Bash",
    description: "Blocks git commits in TypeScript projects if tsc --noEmit fails.",
    why: "Zero TypeScript errors reach your git history. Every commit is type-safe. This is the single highest-ROI hook in the stack.",
    code: `#!/usr/bin/env python3
import json, sys, subprocess, os

data = json.load(sys.stdin)
cmd = data.get('tool_input', {}).get('command', '')

if 'git commit' not in cmd:
    sys.exit(0)

if not (os.path.exists('tsconfig.json') or os.path.exists('package.json')):
    sys.exit(0)

if os.path.exists('tsconfig.json'):
    result = subprocess.run(
        ['npx', 'tsc', '--noEmit'],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        print(f"COMMIT BLOCKED: TypeScript errors found:\\n{result.stderr[:1000]}")
        sys.exit(2)

sys.exit(0)`,
    language: "python",
  },
  {
    name: "Auto-Lint",
    event: "PostToolUse",
    matcher: "Edit|Write",
    description: "Runs TypeScript type checking and ESLint after every file edit.",
    why: "Immediate feedback. Claude sees type errors and lint warnings right after editing, and self-corrects without you having to ask.",
    code: `import json, sys, subprocess, os
data = json.load(sys.stdin)
path = data.get('tool_input', {}).get('file_path', '')
ext = os.path.splitext(path)[1]
results = []
if ext in ['.ts', '.tsx']:
    r = subprocess.run(['npx', 'tsc', '--noEmit'],
        capture_output=True, text=True, timeout=30)
    results.append(r.stderr[:500])
if ext in ['.js', '.jsx', '.ts', '.tsx']:
    r = subprocess.run(['npx', 'eslint', path],
        capture_output=True, text=True, timeout=30)
    results.append(r.stdout[:500])
output = '\\n'.join(r for r in results if r.strip())
if output.strip():
    print(output)`,
    language: "python",
  },
  {
    name: "Session Context",
    event: "SessionStart",
    description: "Injects git status, CLAUDE.md, and open issues at session start.",
    why: "Claude starts every session knowing: what branch you're on, what's changed, what your project context is, and what issues are open.",
    code: `echo '=== Git Status ===' && \\
git status --short 2>/dev/null || echo 'Not a git repo'
echo ''
echo '=== CLAUDE.md ===' && \\
cat CLAUDE.md 2>/dev/null || echo 'No CLAUDE.md'
echo ''
echo '=== Open Issues ===' && \\
gh issue list --limit 5 2>/dev/null || echo 'gh not available'`,
    language: "bash",
  },
  {
    name: "CARL Context Injection",
    event: "UserPromptSubmit",
    description: "Runs the CARL engine to inject context-aware rules on every user message.",
    why: "On every message you send to Claude, CARL measures context, selects a bracket, injects domain rules, routes decisions, and enforces governance.",
    code: `python3 $HOME/.claude/hooks/carl-hook.py`,
    language: "bash",
  },
];

export function getHooksByEvent(event: Hook["event"]): Hook[] {
  return hooks.filter((h) => h.event === event);
}
