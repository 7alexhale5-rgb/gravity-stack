# Skills Catalog

My `~/.claude/skills/` directory has **78 first-class skills** (plus ~100 more contributed by installed plugins). They break into four buckets:

1. **Core workflow stacks** — end-to-end orchestrators that run multi-step pipelines (planning, research, build, review, design, closeout)
2. **Project / session management** — start, resume, pause, handoff, compact
3. **Writing / voice / brand** — copy tuned for each channel
4. **Domain patterns** — libraries, frameworks, stacks (Supabase, Obsidian, Tailwind, testing)

Everything below lives at `~/.claude/skills/<name>/SKILL.md`. Invoke in Claude Code with `/<name>` or via the `Skill` tool.

## Core workflow stacks

These are the backbone. Each takes an intent → produces a verified deliverable. Designed to chain (`planning-stack → build-stack → review-stack → closeout-stack`).

| Skill | What it does |
|---|---|
| `planning-stack` | Multi-source planning with SCATTER/PLAN/VERIFY phases. Auto-runs at `--deep` depth per my CARL rules. |
| `build-stack` | Executes an approved plan with interleaved verification checkpoints, context budget management, and parallel sub-agents for LARGE work. |
| `research-stack` | Multi-source research pipeline (Perplexity, Gemini, Firecrawl, Groq compression). Produces a synthesized report with source attribution. |
| `review-stack` | Four-layer post-implementation review (static, pattern, contextual, runtime). Outputs SHIP IT / FIX / BLOCKED verdict. |
| `design-stack` | UI/UX generation + critique. Figma input path, Playwright verification, multi-variant generation with Muapi, multi-model critique via `/council`. |
| `brainstorm-stack` | Pre-planning questioning pipeline. Runs before planning-stack on high-uncertainty work. |
| `closeout-stack` | End-of-session orchestrator. Replaces the manual `/sc → /handoff → /compound` chain. |

## Planning / debugging / review utilities

| Skill | What it does |
|---|---|
| `compound` | Weekly retrospective. Extracts learnings from git history and session records; feeds them into future planning cycles. |
| `council` | Multi-model advisory board (GPT, Gemini, Grok, DeepSeek). Useful when you want a second opinion without biasing toward Claude. |
| `devilsadvocate` | Standalone claim verification and assumption stress-test. Runs outside the normal pipeline. |
| `dispatch` | "What should I do next?" routing. When stuck mid-task, asks you what phase you're in and points at the right skill. |
| `regression-test` | Golden-dataset eval management via Promptfoo. `init / add / run / report` subcommands. |
| `prompt-engineering` | Checklist + patterns for designing, evaluating, and optimizing LLM prompts. |
| `ship` | Sync branch with base, run tests, push, open PR. |
| `simplify` | Review changed code for reuse + quality; fix detected issues. |

## Project / session management

| Skill | What it does |
|---|---|
| `init-project` | Bootstraps a new project with `.planning/`, `PROJECT.md`, `ROADMAP.md`. |
| `project-connect` | Load project-specific context from a second-brain vault into the session. |
| `project-registry` | Index of all active projects with paths, status, and notes. |
| `project-progress` | Phase-status dashboard rendered in-session. |
| `plan-phase` / `next-phase` / `resume-work` / `pause-work` | Phase-level state machine. |
| `handoff` / `morning-brief` / `close-day` | Day-scale session endpoints. |
| `save` / `sc` | Save to the two-tier memory. `sc` adds compaction afterward. |
| `graduate` | Promote an idea from backlog to a real project. |
| `ideas` | Capture mechanism for the idea backlog. |
| `focus-update` | Weekly priorities interview. |
| `drift` | "Am I drifting off focus?" check against the current-focus doc. |

## Writing, voice, brand

| Skill | What it does |
|---|---|
| `anti-ai-slop-writing` | The filter I run on every public-facing piece of copy. Banned-word list + structural/punctuation/voice rules. |
| `voice-check` | "Does this sound like me?" pass on AI-drafted content. |
| `gig-generator` | Platform-ready gig listing copy from strategy matrix rows. |
| `proposal-generator` | Custom proposals from pasted job posts. |

## Environment / infra

| Skill | What it does |
|---|---|
| `morning-health` | Probe MCP servers, hooks, skills, API keys at session start. |
| `cost-management` | API budget thresholds + emergency response procedures. |
| `cc-channels` | Set up Telegram / Discord / iMessage remote control of CC sessions. |
| `claude-api` | Debug + optimize Anthropic SDK apps. Handles model migrations (4.5 → 4.6 → 4.7). |

## Domain / library patterns

| Skill | What it does |
|---|---|
| `supabase-patterns` | Schema design, RLS policies, React hooks, API routes, pgvector. |
| `obsidian-markdown` / `obsidian-bases` / `obsidian-cli` | Obsidian vault authoring + CLI. |
| `json-canvas` | Author `.canvas` files for Obsidian visual maps. |
| `tailwind-design-system` | Tailwind v4 `@theme` block patterns. |
| `remotion-video-production` | Programmatic video generation. |
| `sentry-cli` | Sentry from the command line. |
| `defuddle` | Clean-markdown scraper — token-efficient alternative to WebFetch. |
| `e2e-testing-patterns` / `javascript-testing-patterns` | Playwright + unit testing. |

## Vault / search

| Skill | What it does |
|---|---|
| `vault-context` | Load context from a personal knowledge vault at session start. |
| `vault-search` | Frontmatter-aware grep across the persistent memory vault. |
| `wiki-compile` / `wiki-lint` / `wiki-query` | Compile sessions into topic-scoped wiki articles. |

## Meta

| Skill | What it does |
|---|---|
| `carl-manager` / `carl-help` | Manage CARL domains + rules. |
| `skill-creator` | Create, update, eval, and benchmark new skills. |
| `writing-skills` | Craft new skills that work before deployment. |
| `find-skills` | Discovery helper for this catalog. |
| `1pct-moves-only` | Productivity override. Suppresses hedging when a plan is already approved. See `toolkit/env/references/1pct-moves-only.md`. |
| `update-config` | Managed edits to `settings.json`. |
| `keybindings-help` | Customize `~/.claude/keybindings.json`. |

## Plugin-provided skills (illustrative, not exhaustive)

Installed plugin marketplaces contribute another ~100 skills. They show up with their plugin prefix:

- `everything-claude-code:*` — 60+ skills covering backend, frontend, database, security, Swift, Django, Spring Boot, TDD, deployment patterns
- `superpowers:*` — brainstorming, executing-plans, dispatching-parallel-agents, test-driven-development, verification-before-completion, writing-skills
- `figma:*` — Figma Code Connect, design-system generation, implementation from Figma, design generation into Figma
- `firecrawl:*` — Web scraping, search, crawling, page interaction
- `coderabbit:*` — Code review + autofix
- `claude-md-management:*` — CLAUDE.md audit + improvement
- `commit-commands:*` — commit / push / open-PR chains
- `claude-code-setup:*` — automation recommender
- `carl:*` — task templates for domain management
- `qodo-skills:*` — rule loading + PR resolver
- `telegram:*`, `figma:*` — integration-specific
- `gsd:*` — a parallel workflow framework with its own phase commands

The pattern: skills you build yourself live in `~/.claude/skills/`, community plugins install to `~/.claude/plugins/` and expose skills prefixed by `pluginname:`.

## Notes for adopters

- Everything here is opt-in. Start with `planning-stack`, `build-stack`, `review-stack`, `closeout-stack` — those four cover 80% of what you'll want.
- Add `anti-ai-slop-writing` the moment you write anything public-facing.
- Add `council` when you want cross-model verification; needs an OpenRouter key.
- The CARL policy engine (`toolkit/env/carl/`) is what binds many of these together — the `manifest` file controls which domain rules load on which prompt keywords.
