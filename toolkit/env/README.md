# toolkit/env/ — shareable Claude Code environment

Drop-in mirror of my actual `~/.claude/` and `~/.carl/` setup, sanitized for public use. Clone this repo, run `toolkit/install.sh`, and your Claude Code comes up with the same agents, hooks, CARL rules, references, and settings skeleton I use daily.

## What's inside

| Path | What | Where it lands |
|---|---|---|
| `agents/` | 9 subagent definitions (Opus, Sonnet, Haiku tiers) pinned to current model IDs | `~/.claude/agents/*.md` |
| `carl/` | CARL policy engine — `manifest` + 6 domain files (global, context, routing, execution, commands, opus-4-7) + a template | `~/.carl/*` |
| `hooks/` | 20 lifecycle hooks — CARL injector, 4D senses, commit gate, closeout guards, media auto-vision | `~/.claude/hooks/*` |
| `references/` | Operating-notes files referenced from CLAUDE.md | `~/.claude/references/*` |
| `skills-catalog.md` | Inventory of my 78 first-class skills + ~100 plugin-provided skills | informational |
| `settings.template.json` | Starter `settings.json` with the hook wiring + permission scaffold | `~/.claude/settings.json` (merge, don't overwrite) |

## Installation

The top-level `toolkit/install.sh` is idempotent. It installs the generic pieces (hooks, agents, CARL) by default and prompts before touching your existing `settings.json` or `CLAUDE.md` files.

```bash
bash toolkit/install.sh
```

To install by hand, copy directories into their destinations:

```bash
cp -n agents/*.md        ~/.claude/agents/
cp -n carl/*             ~/.carl/
cp -n hooks/*            ~/.claude/hooks/
cp -n references/*       ~/.claude/references/
```

Then merge the hook/permission blocks from `settings.template.json` into your own `~/.claude/settings.json`.

## What got redacted

Every file here passes the repo's sanitization test — no VPS IPs, no private project names, no credentials, no personal paths. The shape is real; the specifics are generalized. Colleagues can run this identical env against their own stack.

## Keeping up

When a new model ships, the authoritative behavior notes live in `references/opus-4-7-operating-notes.md` (or its successor). Update that one file; every pointer in CLAUDE.md and the CARL rule set keeps working.

The Opus 4.7 migration has its own focused companion kit at:
**<https://github.com/7alexhale5-rgb/opus-4-7-playbook>**
