# The Gravity Stack

> **The complete blueprint for a top 1% AI-native development environment.**

By Alex Hale & Claude · MIT License · 2026

---

## What's new

**2026-09-29: Current models and the development process.** Agents and configs now pin the current lineup: `claude-opus-5-5` (default), `claude-sonnet-5-5` and `claude-haiku-4-5`, with `claude-fable-5-1` named for the hardest work. The Opus 4.7 docs stay as history. A new [Development process](#development-process) section points to the development-protocol repo, and `toolkit/install.sh` can install it as an optional step. Full list in [CHANGELOG.md](CHANGELOG.md).

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

## Current models

Checked against Anthropic's models overview on 2026-09-29.

| Model             | ID                  | Use it for                           |
| ----------------- | ------------------- | ------------------------------------ |
| Claude Fable 5.1  | `claude-fable-5-1`  | Hardest reasoning, long agentic work |
| Claude Opus 5.5   | `claude-opus-5-5`   | Default for most work                |
| Claude Sonnet 5.5 | `claude-sonnet-5-5` | Speed and intelligence               |
| Claude Haiku 4.5  | `claude-haiku-4-5`  | Fastest                              |

Legacy: Opus 4.8, 4.7, 4.6, 4.5, Opus 5, Fable 5, Sonnet 5, 4.6, 4.5. The Opus 4.7 pages in this repo are kept as history.

## Development process

How work moves from idea to shipped code now lives in one place: the [development-protocol](https://github.com/7alexhale5-rgb/development-protocol) repo. It holds 19 skills, a 17-row evidence checklist, and an installer. Every task follows the same spine: **spec, build, verify, close.** You pin the goal and plan it, build one slice at a time with a check after each, prove the change on the real thing with a second reviewer, then commit, ship and write the handoff. A step counts as done only when an evidence file exists and a check command passes. Install it with:

```bash
git clone https://github.com/7alexhale5-rgb/development-protocol.git
cd development-protocol
./install.sh            # Claude Code and Codex; add --target claude or --target codex to pick one
```

Or say yes to the optional step in `bash toolkit/install.sh`. Read [STANDARD.md](https://github.com/7alexhale5-rgb/development-protocol/blob/main/docs/STANDARD.md) for what "done" means and [WORKFLOW.md](https://github.com/7alexhale5-rgb/development-protocol/blob/main/docs/WORKFLOW.md) for how the work flows day to day. Those docs are not copied here, so there is one source of truth.

## Quick start

### Clone + run the installer

```bash
git clone https://github.com/7alexhale5-rgb/gravity-stack.git
cd gravity-stack
bash toolkit/install.sh
```

The installer is idempotent — safe to re-run any time. Phases 1 to 5 detect what is already
installed or configured and skip it rather than overwrite it; the only interactive prompt is the
optional Phase 6 step below.

Flags: `--dry-run` prints what would happen and changes nothing. `--yes` says yes to the optional development-protocol step. `--skip-dev-protocol` leaves that step out.

### Or cherry-pick from toolkit/env/

Each subdirectory is independently useful:

```bash
# Just drop in the CARL domain files
cp toolkit/env/carl/* ~/.carl/

# Just pin your subagents to explicit model IDs
cp toolkit/env/agents/*.md ~/.claude/agents/

# Just install the Opus 4.7 behavior rules (historical)
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
│   ├── opus-4-7.md              # Companion-kit pointer (historical)
│   ├── environment-audit-2026-03.md  # Deep peer-comparison inventory (historical)
│   ├── design-system.md
│   └── troubleshooting.md
├── tests/
│   ├── test_sanitization.sh     # CI-enforced leak detector
│   └── sanitization-patterns.txt
├── .promptfoo/                  # Golden-dataset regression tests
├── design-system/               # Design tokens
├── CHANGELOG.md
├── CLAUDE.md
├── LICENSE
└── README.md
```

## Documentation

| Page                                                             | Description                                                                                   |
| ---------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| [Opus 4.7](docs/opus-4-7.md)                                     | Historical. Companion kit pointer + 30-second orientation                                     |
| [Environment audit (2026-03)](docs/environment-audit-2026-03.md) | Historical. Deep peer-comparison inventory — plugins, MCPs, hooks, skills, CARL rules, agents |
| [CARL](docs/carl.md)                                             | Governance engine deep-dive                                                                   |
| [Hooks](docs/hooks.md)                                           | Lifecycle hooks with code                                                                     |
| [Skills](docs/skills.md)                                         | Catalog and invocation patterns                                                               |
| [Plugins](docs/plugins.md)                                       | Marketplace plugins with priorities                                                           |
| [MCP Servers](docs/mcp-servers.md)                               | Server configs and setup guides                                                               |
| [Design System](docs/design-system.md)                           | Typography, colors, components                                                                |
| [Troubleshooting](docs/troubleshooting.md)                       | Common issues and fixes                                                                       |

The Next.js site in `site/` renders the same material with search, navigation, and a manifesto.

## Companion repo

**[opus-4-7-playbook](https://github.com/7alexhale5-rgb/opus-4-7-playbook)** is the focused migration kit for the Opus 4.7 release (2026-04). It is kept as history; current models are listed above. It has runnable Python examples, migration scripts, per-project CLAUDE.md snippets, and Instagram carousel source code. Install it standalone or use it alongside gravity-stack.

Rule of thumb:

- **Gravity Stack** = the whole environment (agents, hooks, CARL, references, skills catalog)
- **Playbook** = the migration kit for Opus 4.7 (historical)

Both are MIT, both pass sanitization in CI, both are designed to be forked and adapted.

## Tech stack

| Technology   | Version | Notes                      |
| ------------ | ------- | -------------------------- |
| Next.js      | 16      | App Router, Turbopack      |
| Tailwind CSS | 4.2     | CSS-based `@theme` config  |
| shadcn/ui    | Latest  | Dark theme, New York style |
| TypeScript   | Strict  | Built into Next.js 16      |
| shiki        | Latest  | Syntax highlighting        |

## Prerequisites

| Requirement  | Minimum             | Recommended   |
| ------------ | ------------------- | ------------- |
| macOS        | Ventura 13.0+       | Sequoia 15.0+ |
| Architecture | Apple Silicon (M1+) | M2 Pro / M3+  |
| Node.js      | 20.9                | 22 LTS        |
| Python       | 3.10                | 3.12          |
| Claude Code  | Latest              | Latest        |
| Subscription | Claude Pro          | Claude Max    |

## Contributing

Fork, branch, make your changes, then:

1. `bash tests/test_sanitization.sh` must return `clean`
2. `cd site && npm run build` must produce zero errors
3. Open a PR

The sanitization test blocks PRs that leak personal paths, VPS IPs, API keys, or private project codenames. See [`tests/sanitization-patterns.txt`](tests/sanitization-patterns.txt) for the full list.

## License

MIT. See [LICENSE](LICENSE).

---

_Built by humans and AI, working together._
