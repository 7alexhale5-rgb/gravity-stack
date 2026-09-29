# Gravity Stack

## Where to go

This repo follows ICM (Jake Van Clief's folder method): this file routes, each room's
`CONTEXT.md` holds its contract.

| Task                                                   | Go to        | Read                                         | Skills            |
| ------------------------------------------------------ | ------------ | -------------------------------------------- | ----------------- |
| Change a docs-site route, component, or the data layer | `site/`      | [site/CONTEXT.md](site/CONTEXT.md)           | none              |
| Change or run a setup script                           | `toolkit/`   | [toolkit/CONTEXT.md](toolkit/CONTEXT.md)     | none              |
| Write or update a deep-dive doc                        | `docs/`      | [docs/CONTEXT.md](docs/CONTEXT.md)           | none              |
| Pick up or update the implementation plan              | `.planning/` | [.planning/CONTEXT.md](.planning/CONTEXT.md) | `/planning-stack` |

Root files stay where their tools expect them: `LICENSE` (public repo requirement),
`README.md`/`CHANGELOG.md` (public-facing), `.promptfoo/` (eval harness, its own
`promptfooconfig.yaml`). `.promptfoo/`, `design-system/`, `routines/` are not yet ICM rooms —
read them directly.

## Naming

TypeScript/TSX camelCase in `site/`, kebab-case docs, shell scripts snake/kebab in `toolkit/`.

## Models

Current models (2026-09-29): Claude Opus 5.5 `claude-opus-5-5` is the default, Claude Fable 5.1 `claude-fable-5-1` handles the hardest reasoning and long agentic work, Claude Sonnet 5.5 `claude-sonnet-5-5` balances speed and intelligence, and Claude Haiku 4.5 `claude-haiku-4-5` is the fastest. See README for the full list.

The Opus 4.7 notes at `toolkit/env/references/opus-4-7-operating-notes.md` and the companion repo `https://github.com/7alexhale5-rgb/opus-4-7-playbook` are kept as history.

## Overview
Open-source documentation site + setup toolkit for AI-native development environments.

## Tech Stack
- **Site:** Next.js 16, Tailwind v4, shadcn/ui, TypeScript strict
- **Fonts:** Instrument Serif (heading), Satoshi (body), DM Mono (code)
- **Deployment:** Vercel
- **License:** MIT

## Project Structure
```
gravity-stack/
├── site/           # Next.js 16 documentation site (11 routes)
├── toolkit/        # Automated setup scripts (idempotent)
├── docs/           # Deep-dive markdown documentation
├── .planning/      # Implementation guide and planning docs
└── LICENSE          # MIT
```

## Conventions
- Tailwind v4 uses CSS `@theme` blocks — NO tailwind.config.ts
- Server Components by default, Client only when interactivity is required
- Data layer in `site/src/lib/data/` is the single source of truth
- All toolkit scripts are idempotent (check before installing)

## Commands
```bash
cd site && npm run dev    # Development server
cd site && npm run build  # Production build
```

## Attribution
By Alex Hale & Claude
