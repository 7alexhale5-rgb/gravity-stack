# Hooks

Hook scripts run at Claude Code lifecycle events. Bundled sources are in
[`toolkit/env/hooks/`](../toolkit/env/hooks/). The default installer copies only
`toolkit/configs/commit-gate.py`; optional hooks need manual selection and dependency checks.

## Current command-hook contract

Claude passes a JSON object on **stdin**. Read `tool_input.command` for Bash,
`tool_input.file_path` for Edit/Write, and `cwd` for the project directory. Legacy
`MCP_TOOL_INPUT_*` variables are not the input contract.

For `PreToolUse`, exit **2** blocks the operation and stderr supplies the reason.
Exit 1 is a nonblocking error. Exit 0 normally allows; a valid structured permission
response may instead deny. See the [official hook reference](https://code.claude.com/docs/en/hooks).
A hook cannot replace CI, branch protection or a human's approval.

## Settings shape

A matcher contains a nested `hooks` list. This registers the installed commit gate:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 $HOME/.claude/hooks/commit-gate.py",
            "timeout": 70
          }
        ]
      }
    ]
  }
}
```

Merge into existing settings, do not replace unrelated entries. The compiler itself
has a 60-second timeout. Select a hook timeout longer than that to receive its verdict.
The phase-5 check verifies the script and Bash registration, not live firing.

## Available examples

| Hook                | Event                      | Default install        | Proof needed                                                           |
| ------------------- | -------------------------- | ---------------------- | ---------------------------------------------------------------------- |
| Commit gate         | PreToolUse / Bash          | Yes                    | Failing compiler blocks with exit 2                                    |
| File guard          | PreToolUse / Edit or Write | Starter inline command | Protected path blocks with stdin JSON                                  |
| Notification        | Notification               | Starter command        | macOS alert appears                                                    |
| Session backup      | PreCompact                 | Starter command        | Input transcript exists and saved copy matches                         |
| Auto-lint           | PostToolUse                | Manual                 | Diagnostics refer to the edited file                                   |
| Session context     | SessionStart               | Starter command        | Git and issue access verified separately                               |
| CARL rule injection | UserPromptSubmit           | Manual                 | Required rule files and dependencies exist; actual context is observed |

The starter backup command expects `~/.claude/current-session.jsonl`; that file is
not guaranteed to exist. Select the bundled stdin-aware backup hook if its dependencies
fit your environment. A directory alone does not prove a working backup.

## Test before using

Use a disposable project. Feed the same JSON shape Claude provides. This example checks
a commit failure without making a commit: put a failing `npx` fixture on PATH, create a
`tsconfig.json`, and run:

```bash
printf '%s\n' '{"tool_name":"Bash","tool_input":{"command":"git commit -m test"}}' |
  python3 "$HOME/.claude/hooks/commit-gate.py"
```

Read the exit code and stderr. A failed compiler must return 2. A successful compiler
must return 0. Also test a noncommit command, unavailable compiler and timeout.
`tests/test_hook_safety.py` performs these checks without running destructive Git commands.
Then verify a real Claude session invokes the selected hook. Script tests alone do not prove
that the host loaded it.

## Boundaries

The destructive-command hook blocks selected dangerous shell forms. It does not parse every
possible shell program. The file guard covers Edit/Write paths, not all shell writes.
Lease pushes require a positional repository and a literal explicit destination such as
`feature:refs/heads/feature`. Implicit destinations can follow repository mappings, so they
are refused. Lease pushes using `--repo`, extra-destination or deletion options (`--all`,
`--tags`, `--follow-tags`, `--prune`, `--delete`), abbreviated or unknown push options, wildcard refs,
or the protected destinations `main`, `master` and `HEAD` are refused. Ordinary pushes
using the supported full option names remain allowed. Quoted or escaped punctuation is
treated as a literal argument; actual shell separators still divide commands.
Keep credentials outside tracked settings and process arguments. Review optional model calls
against your data rules and budget before enabling them.
