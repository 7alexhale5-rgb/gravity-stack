# The Gravity Stack

> **The complete blueprint for a top 1% AI-native development environment.**

By Alex Hale & Claude · MIT License · 2026

---

## What's new

**2026-04-16 — Opus 4.7 alignment.** The env is now aligned to Claude Opus 4.7 (released 2026-04-16). CARL ships a new always-on `opus-4-7` domain encoding the 7 behavior rules; agents are pinned to explicit model IDs (`claude-opus-4-7` / `claude-sonnet-4-6` / `claude-haiku-4-5`); a single `opus-4-7-operating-notes.md` file is the source of truth, referenced from global + per-project CLAUDE.md. The focused migration kit — docs, templates, runnable examples, Instagram carousel source — lives in a companion repo for shareability: **[opus-4-7-playbook](https://github.com/7alexhale5-rgb/opus-4-7-playbook)**.

## What is this?

Gravity Stack documents a production AI-native development environment built on Claude Code. The current snapshot:

- **35+ plugins** across official and custom marketplaces (installed, pinned, categorized)
- **10+ MCP servers** — browser automation, web scraping, search, memory, knowledge bases
- **20 lifecycle hooks** — CARL injection, 4D senses, commit gates, closeout guards, media auto-vision, design-decision capture
- **78 first-class skills** + ~100 plugin-provided skills across 14 categories. Full catalog: [`toolkit/env/skills-catalog.md`](toolkit/env/skills-catalog.md)
- **CARL engine** — a ~1,700-line Python governance engine with context brackets, 6 domain rules, and the planning router
- **9 specialized agents** across Opus, Sonnet, and Haiku tiers

Every configuration in this repo is either my actual working config or a sanitized-to-share version of it. The sanitization test (CI-enforced) makes sure nothing personal leaks through.

## Quick start

### Clone + run the installer

```bash
git clone https://github.com/7alexhale5-rgb/gravity-stack.git
cd gravity-stack
bash toolkit/install.sh
```

The installer is idempotent — safe to re-run any time. It prompts before touching files that already exist.

### Or cherry-pick from toolkit/env/

Each subdirectory is independently useful:

```bash
# Just drop in the CARL domain files
cp toolkit/env/carl/* ~/.carl/

# Just pin your subagents to explicit model IDs
cp toolkit/env/agents/*.md ~/.claude/agents/

# Just install the Opus 4.7 behavior rules
cp toolkit/env/references/opus-4-7-operating-notes.md ~/.claude/references/
```

Read [`toolkit/env/README.md`](toolkit/env/README.md) for what lands where.

### Browse the docs site

```bash
cd site
npm install
npm run dev
```

Visit `http://localhost:3000`.

## Project structure

```
gravity-stack/
├── site/                       # Next.js 16 documentation site
├── toolkit/
│   ├── install.sh              # Master installer (idempotent)
│   ├── scripts/                # Phase scripts
│   ├── configs/                # Template configs
│   ├── templates/              # CLAUDE.md template
│   ├── vault-search.sh         # Frontmatter-aware vault search
│   └── env/                    # Drop-in env mirror (agents, CARL, hooks, references)
├── docs/
│   ├── carl.md
│   ├── hooks.md
│   ├── skills.md
│   ├── plugins.md
│   ├── mcp-servers.md
│   ├── opus-4-7.md              # Companion-kit pointer
│   ├── environment-audit-2026-03.md  # Deep peer-comparison inventory
│   ├── design-system.md
│   └── troubleshooting.md
├── tests/
│   ├── test_sanitization.sh     # CI-enforced leak detector
│   └── sanitization-patterns.txt
├── .promptfoo/                  # Golden-dataset regression tests
├── design-system/               # Design tokens
├── CLAUDE.md
├── LICENSE
└── README.md
```

## Documentation

| Page | Description |
|------|-------------|
| [Opus 4.7](docs/opus-4-7.md) | Companion kit pointer + 30-second orientation |
| [Environment audit (2026-03)](docs/environment-audit-2026-03.md) | Deep peer-comparison inventory — plugins, MCPs, hooks, skills, CARL rules, agents |
| [CARL](docs/carl.md) | Governance engine deep-dive |
| [Hooks](docs/hooks.md) | Lifecycle hooks with code |
| [Skills](docs/skills.md) | Catalog and invocation patterns |
| [Plugins](docs/plugins.md) | Marketplace plugins with priorities |
| [MCP Servers](docs/mcp-servers.md) | Server configs and setup guides |
| [Design System](docs/design-system.md) | Typography, colors, components |
| [Troubleshooting](docs/troubleshooting.md) | Common issues and fixes |

The Next.js site in `site/` renders the same material with search, navigation, and a manifesto.

## Companion repo

**[opus-4-7-playbook](https://github.com/7alexhale5-rgb/opus-4-7-playbook)** is the focused migration kit for the current model release. It has runnable Python examples, migration scripts, per-project CLAUDE.md snippets, and Instagram carousel source code. Install it standalone or use it alongside gravity-stack.

Rule of thumb:

- **Gravity Stack** = the whole environment (agents, hooks, CARL, references, skills catalog)
- **Playbook** = the migration kit for the current model

Both are MIT, both pass sanitization in CI, both are designed to be forked and adapted.

## Tech stack

| Technology | Version | Notes |
|-----------|---------|-------|
| Next.js | 16 | App Router, Turbopack |
| Tailwind CSS | 4.2 | CSS-based `@theme` config |
| shadcn/ui | Latest | Dark theme, New York style |
| TypeScript | Strict | Built into Next.js 16 |
| shiki | Latest | Syntax highlighting |

## Prerequisites

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| macOS | Ventura 13.0+ | Sequoia 15.0+ |
| Architecture | Apple Silicon (M1+) | M2 Pro / M3+ |
| Node.js | 20.9 | 22 LTS |
| Python | 3.10 | 3.12 |
| Claude Code | Latest | Latest |
| Subscription | Claude Pro | Claude Max |

## Contributing

Fork, branch, make your changes, then:

1. `bash tests/test_sanitization.sh` must return `clean`
2. `cd site && npm run build` must produce zero errors
3. Open a PR

The sanitization test blocks PRs that leak personal paths, VPS IPs, API keys, or private project codenames. See [`tests/sanitization-patterns.txt`](tests/sanitization-patterns.txt) for the full list.

## License

MIT. See [LICENSE](LICENSE).

---

*Built by humans and AI, working together.*
