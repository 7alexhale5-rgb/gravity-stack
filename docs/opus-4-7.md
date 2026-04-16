# Opus 4.7

Claude Opus 4.7 shipped 2026-04-16. Five API params that worked on 4.6 now return HTTP 400. One silent default makes streaming UIs look hung. The new tokenizer uses up to 35% more tokens for the same input. Most setups need a migration pass, not a swap.

The env pieces for 4.7 (CARL domain, operating notes, agent pinning pattern) are already bundled in `toolkit/env/`. The focused migration kit — docs, templates, working examples, interactive installer, social assets — lives in its own repo so it can stand alone and get indexed/shared independently:

**Companion kit:** <https://github.com/7alexhale5-rgb/opus-4-7-playbook>

## 30-second orientation

- **Breaking changes:** `temperature`, `top_p`, `top_k`, `thinking.budget_tokens`, assistant prefill. All return 400.
- **New API shape:** `thinking: {type: "adaptive"}` + `output_config.effort: "xhigh"` replaces extended thinking + the integer budget dial.
- **New effort level:** `xhigh` slots between `high` and `max`. Intended default for coding and agentic loops. 4.7 respects `low` / `medium` more strictly than 4.6.
- **Silent default:** `thinking.display` flipped from shown → `"omitted"`. If your UI streams reasoning, set `"summarized"` explicitly.
- **Tokenizer:** 1.0–1.35× more tokens per input. Raise `max_tokens` by ≥35%. Minimum 64,000 at `xhigh` / `max`.
- **Task budgets (beta):** advisory token countdown across a full agentic loop. Min 20k. Messages API only (not Claude Code / Cowork yet).

## What's in `toolkit/env/` for 4.7

- `carl/opus-4-7` — always-on CARL domain encoding the 7 behavior rules. Registered in `carl/manifest` with `OPUS-4-7_STATE=active` and `OPUS-4-7_ALWAYS_ON=true`.
- `references/opus-4-7-operating-notes.md` — full migration checklist and behavior notes. Referenced from your global `CLAUDE.md` so every session inherits the guidance.
- `agents/*.md` — all 9 agents pinned to explicit model IDs (`claude-opus-4-7`, `claude-sonnet-4-6`, `claude-haiku-4-5`). Pin rather than alias so an alias change at Anthropic doesn't silently re-route production-critical paths.

## Full migration (external codebases)

For code outside Claude Code — your own SDK apps, agentic runtimes, vision pipelines — use the companion kit. It has:

- Runnable Python examples (minimal call, agentic loop, task-budget wrapper, full-resolution vision)
- Migration scripts (`pin-agents.sh`, `grep-for-deprecated.sh`, interactive `install.sh`)
- CI-enforced sanitization + syntax + link tests
- Instagram carousel source (Vite + React + Tailwind) for sharing the migration takeaway

Clone:
```bash
git clone https://github.com/7alexhale5-rgb/opus-4-7-playbook
```

Or in Claude Code, the bundled `claude-api` skill automates most of the Messages-API edits:
```
/claude-api migrate this project to claude-opus-4-7
```
