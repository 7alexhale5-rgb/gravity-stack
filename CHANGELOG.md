# Changelog

## 2026-10-26

### Models and config

- Current lineup is Opus 5.5 `claude-opus-5-5`, Sonnet 5.5 `claude-sonnet-5-5` and Haiku 5.5 `claude-haiku-5-5` (Fable 5.1 `claude-fable-5-1` for the hardest work). Haiku 4.5 is legacy.
- Agents: scout and quickfix moved from `claude-haiku-4-5` to `claude-haiku-5-5`; implementer, research and tester moved from `claude-opus-5-5` to `claude-sonnet-5-5` (Sonnet is the default lane for implementation work).
- Hooks: model-aware context window in `token_budget.py` and `carl-hook.py`, Groq client repin and bounded retry, a dead-letter queue for `extract_memories.py`, and a design nudge that now reaches the model.

### Docs

- New deep-dive `docs/chief-of-staff.md`: the chief-of-staff operating model for multi-stream work. The chief of staff directs and builds nothing; each stream runs as its own session that outlives it; each session uses subagent-driven development; every task goes to the narrowest agent type; one owner per PR and one merger per repo. Covers the CoS files (roster, common brief, state log, resume prompt, unfinished-work register), the failure modes (lanes stop at session close, usage limits and network drops, unreliable auto-continue, blocking questions, records that must leave the laptop) and the daily and weekly upkeep. Generic: no client or personal data.
- README: added the page to the project tree and the Documentation table. `docs/CONTEXT.md` Inputs lists it.

## 2026-09-29

### Models

- Pinned agents moved to the current lineup: `claude-opus-4-7` to `claude-opus-5-5` (architect, implementer, research, reviewer, supabase, tester) and `claude-sonnet-4-6` to `claude-sonnet-5-5` (stakeholder-reviewer). Haiku agents stay on `claude-haiku-4-5`.
- Promptfoo golden tests moved from `claude-sonnet-4-20250514` to `claude-sonnet-5-5` (main config and the four per-skill configs).
- Removed `temperature: 0` from all 5 promptfoo configs: `claude-sonnet-5-5` returns HTTP 400 on any non-default `temperature`/`top_p`/`top_k`.
- CARL `opus-4-7` domain: RULE_0 now names the current model IDs, including `claude-fable-5-1` for the hardest work. Added a successor note. Rules 1 to 6 still describe Opus 4.7 and were not rewritten.
- CARL `manifest`: added a successor note to the `opus-4-7` entry.
- `CLAUDE.md`: the Opus 4.7 section is replaced by a short Models section with the current lineup.
- Marked as history with one line at the top, content unchanged: `docs/opus-4-7.md`, `docs/environment-audit-2026-03.md`, `toolkit/env/references/opus-4-7-operating-notes.md`.

### Development process

- README: new "What's new" entry, a "Current models" table, and a "Development process" section that links to the development-protocol repo, its STANDARD.md and WORKFLOW.md, with install commands.
- README: Opus 4.7 pages and the companion playbook are labeled as history. Installer flags are listed.
- `toolkit/install.sh`: new flags `--dry-run`, `--yes` and `--skip-dev-protocol`. New optional Phase 6 asks whether to clone the development-protocol repo to a temp folder and run its `./install.sh --yes`. With no terminal to ask on, it skips unless `--yes` is given. A failed clone or install warns and does not stop the rest of the install. `--dry-run` prints each step and changes nothing, including the Phase 6 prompt.

### Round 3 review fixes

- `toolkit/install.sh`: Phase 6 now forwards `--target` to the inner development-protocol
  `./install.sh` instead of always installing Claude-only. Defaults to `claude`, and to `both` when
  this machine already has a Codex skills root (`~/.agents`).
- `.gitignore`: added `.claude/` (local, machine-specific Claude Code settings; never shareable).
- README: the installer no longer claims it "prompts before touching files that already exist" --
  Phases 1 to 5 are idempotent and skip what is already there; only the optional Phase 6 step
  prompts. Reworded to say that.
- `tests/sanitization-patterns.txt`: removed the "Private project codenames" list -- publishing
  client and internal codenames in the same file meant to catch them was self-defeating. They now
  live in a file kept outside this repo, read via `GRAVITY_PRIVATE_PATTERNS`
  (`tests/test_sanitization.sh` reads it the same way repo A's `DEVPROTO_PRIVATE_PATTERNS` works).
  Going forward only; the names already in git history are a separate, human decision.

### Log

- Added this CHANGELOG.
