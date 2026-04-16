# Hooks

> **Canonical hook sources:** [`../toolkit/env/hooks/`](../toolkit/env/hooks/). 20 lifecycle hooks covering CARL injection, 4D senses, commit gates, closeout guards, media auto-vision, design decision capture.

Hooks are event-driven scripts that run automatically at specific points in a Claude Code session. They let you enforce rules, automate tasks, and inject context without manual intervention. Hooks are configured in `~/.claude/settings.json` under the `hooks` key.

## Hook Events

| Event | When It Fires | Use Case |
|-------|--------------|----------|
| `PreToolUse` | Before Claude runs a tool | Block dangerous operations |
| `PostToolUse` | After Claude runs a tool | Run linters, formatters |
| `PreCompact` | Before context compaction | Save session transcripts |
| `SessionStart` | When a new session begins | Inject project context |
| `UserPromptSubmit` | When the user sends a message | Governance, routing |
| `Notification` | When Claude needs user input | Desktop alerts |

## The 7 Hooks

### 1. Notification

Send a macOS notification when Claude finishes a task and needs your input. Essential when you context-switch while Claude works.

**Event**: `Notification`

```json
{
  "hooks": {
    "Notification": [
      {
        "type": "command",
        "command": "osascript -e 'display notification \"Claude needs your attention\" with title \"Claude Code\"'"
      }
    ]
  }
}
```

**Why it matters**: Claude often completes multi-step tasks in seconds. Without notifications, you waste time checking back manually. This hook keeps you in flow.

---

### 2. Session Backup

Save the full session transcript before Claude compacts context. Compaction is irreversible and discards older messages to free up context window space. This hook preserves the full record.

**Event**: `PreCompact`

```json
{
  "hooks": {
    "PreCompact": [
      {
        "type": "command",
        "command": "cp ~/.claude/sessions/current.json ~/.claude/backups/session-$(date +%Y%m%d-%H%M%S).json"
      }
    ]
  }
}
```

**Why it matters**: Compaction throws away context to make room for new work. If you need to review what happened earlier in a long session, the backup is your safety net. Without it, that context is gone permanently.

---

### 3. File Guard

Block edits to sensitive files that should never be modified by an AI agent. Prevents accidental overwrites of environment variables, lock files, git internals, and database migrations.

**Event**: `PreToolUse`
**Matcher**: `Edit|Write`

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "type": "command",
        "matcher": "Edit|Write",
        "command": "node -e \"const p = process.env.MCP_TOOL_INPUT_FILE_PATH || ''; const blocked = ['.env', 'package-lock.json', '.git/', 'supabase/migrations/']; if (blocked.some(b => p.includes(b))) { console.error('BLOCKED: protected file'); process.exit(1); }\""
      }
    ]
  }
}
```

**Protected paths**:
- `.env` -- Environment variables with secrets
- `package-lock.json` -- Dependency lock file (use npm/bun to modify)
- `.git/` -- Git internals
- `supabase/migrations/` -- Database migrations (use Supabase CLI)

**Why it matters**: A single bad edit to `.env` can leak secrets. A modified `package-lock.json` can introduce supply chain issues. Migrations should go through the Supabase CLI, not direct file edits. This hook makes these mistakes impossible.

---

### 4. Commit Gate

Block git commits if the TypeScript compiler reports errors. Prevents shipping broken code.

**Event**: `PreToolUse`
**Matcher**: `Bash`

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "type": "command",
        "matcher": "Bash",
        "command": "node -e \"const cmd = process.env.MCP_TOOL_INPUT_COMMAND || ''; if (cmd.includes('git commit')) { try { require('child_process').execFileSync('npx', ['tsc', '--noEmit'], { stdio: 'pipe' }); } catch(e) { console.error('BLOCKED: TypeScript errors found.'); process.exit(1); } }\""
      }
    ]
  }
}
```

**Why it matters**: Claude can write code that looks correct but has type errors. This hook catches those errors before they enter the git history. It is faster and more reliable than remembering to run `tsc` manually.

---

### 5. Auto-Lint

Automatically run TypeScript type checking and ESLint after any file edit. Catches errors immediately instead of discovering them later.

**Event**: `PostToolUse`
**Matcher**: `Edit|Write`

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "type": "command",
        "matcher": "Edit|Write",
        "command": "node -e \"const p = process.env.MCP_TOOL_INPUT_FILE_PATH || ''; if (p.endsWith('.ts') || p.endsWith('.tsx')) { const cp = require('child_process'); try { cp.execFileSync('npx', ['tsc', '--noEmit'], { stdio: 'pipe' }); } catch(e) { console.log('TSC errors found'); } try { cp.execFileSync('npx', ['eslint', p, '--no-warn-ignored'], { stdio: 'pipe' }); } catch(e) { console.log('ESLint issues found'); } }\""
      }
    ]
  }
}
```

**Why it matters**: Without immediate feedback, Claude can introduce an error in step 2 that does not surface until step 10. By linting after every edit, errors are caught and fixed in context, while the relevant code is still fresh.

---

### 6. Session Context

Inject project context at the start of every session. Automatically provides git status, the project's `CLAUDE.md`, and open GitHub issues so Claude starts with full awareness.

**Event**: `SessionStart`

```json
{
  "hooks": {
    "SessionStart": [
      {
        "type": "command",
        "command": "echo '--- Git Status ---' && git status --short 2>/dev/null && echo '--- CLAUDE.md ---' && cat CLAUDE.md 2>/dev/null && echo '--- Open Issues ---' && gh issue list --limit 5 --state open 2>/dev/null || true"
      }
    ]
  }
}
```

**Why it matters**: Every session starts cold. Without this hook, you spend the first few messages getting Claude up to speed on what branch you are on, what is changed, and what needs to be done. This hook eliminates that warmup overhead.

---

### 7. CARL Context Injection

Run the CARL governance engine on every user prompt. CARL measures remaining context, selects the appropriate governance bracket, and injects rules that guide Claude's behavior.

**Event**: `UserPromptSubmit`

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "type": "command",
        "command": "python3 ~/.claude/carl/carl_engine.py"
      }
    ]
  }
}
```

**Why it matters**: CARL prevents Claude from wasting context on the wrong approach. When context is fresh, Claude can plan ambitiously. When context is depleted, CARL forces conservative behavior and subagent delegation. Without CARL, you get no governance and sessions degrade unpredictably as context fills up.

---

## Full Configuration

Here is the complete `hooks` block for `~/.claude/settings.json`:

```json
{
  "hooks": {
    "Notification": [
      {
        "type": "command",
        "command": "osascript -e 'display notification \"Claude needs your attention\" with title \"Claude Code\"'"
      }
    ],
    "PreCompact": [
      {
        "type": "command",
        "command": "cp ~/.claude/sessions/current.json ~/.claude/backups/session-$(date +%Y%m%d-%H%M%S).json"
      }
    ],
    "PreToolUse": [
      {
        "type": "command",
        "matcher": "Edit|Write",
        "command": "node -e \"const p = process.env.MCP_TOOL_INPUT_FILE_PATH || ''; const blocked = ['.env', 'package-lock.json', '.git/', 'supabase/migrations/']; if (blocked.some(b => p.includes(b))) { console.error('BLOCKED: protected file'); process.exit(1); }\""
      },
      {
        "type": "command",
        "matcher": "Bash",
        "command": "node -e \"const cmd = process.env.MCP_TOOL_INPUT_COMMAND || ''; if (cmd.includes('git commit')) { try { require('child_process').execFileSync('npx', ['tsc', '--noEmit'], { stdio: 'pipe' }); } catch(e) { console.error('BLOCKED: TypeScript errors found.'); process.exit(1); } }\""
      }
    ],
    "PostToolUse": [
      {
        "type": "command",
        "matcher": "Edit|Write",
        "command": "node -e \"const p = process.env.MCP_TOOL_INPUT_FILE_PATH || ''; if (p.endsWith('.ts') || p.endsWith('.tsx')) { const cp = require('child_process'); try { cp.execFileSync('npx', ['tsc', '--noEmit'], { stdio: 'pipe' }); } catch(e) { console.log('TSC errors found'); } try { cp.execFileSync('npx', ['eslint', p, '--no-warn-ignored'], { stdio: 'pipe' }); } catch(e) { console.log('ESLint issues found'); } }\""
      }
    ],
    "SessionStart": [
      {
        "type": "command",
        "command": "echo '--- Git Status ---' && git status --short 2>/dev/null && echo '--- CLAUDE.md ---' && cat CLAUDE.md 2>/dev/null && echo '--- Open Issues ---' && gh issue list --limit 5 --state open 2>/dev/null || true"
      }
    ],
    "UserPromptSubmit": [
      {
        "type": "command",
        "command": "python3 ~/.claude/carl/carl_engine.py"
      }
    ]
  }
}
```

## Writing Custom Hooks

### Rules

1. **Exit code 0** means success (allow the operation to proceed)
2. **Exit code non-zero** means failure (block the operation for `Pre*` hooks)
3. **stdout** is captured and shown to Claude as context
4. **stderr** is captured and shown as error messages
5. Hooks run synchronously and block the operation until complete
6. Keep hooks fast (under 5 seconds) to avoid degrading the experience

### Environment Variables

Hooks receive context through environment variables:

| Variable | Available In | Description |
|----------|-------------|-------------|
| `MCP_TOOL_INPUT_COMMAND` | `PreToolUse` (Bash) | The bash command about to run |
| `MCP_TOOL_INPUT_FILE_PATH` | `PreToolUse` (Edit/Write) | The file path being edited |
| `MCP_TOOL_INPUT_file_path` | `PreToolUse` (Edit/Write) | Alternate casing for file path |
| `MCP_TOOL_OUTPUT` | `PostToolUse` | The tool's output |

### Testing Hooks

Test a hook manually before adding it to settings:

```bash
# Simulate a PreToolUse Edit hook
MCP_TOOL_INPUT_FILE_PATH=".env" node -e "const p = process.env.MCP_TOOL_INPUT_FILE_PATH; if (p.includes('.env')) { console.error('BLOCKED'); process.exit(1); }"
```

If it exits with code 1 and prints "BLOCKED", the hook works correctly.
