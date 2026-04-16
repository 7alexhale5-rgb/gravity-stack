# Gravity Stack

## Opus 4.7 Operating Notes

This project operates on Claude Opus 4.7 (released 2026-04-16). Behavior: adaptive-only thinking, literal instruction-following, calibrated response length, no `temperature`/`top_p`/`top_k`. Full reference: `~/.claude/references/opus-4-7-operating-notes.md` (canonical copy mirrored into this repo at `toolkit/env/references/opus-4-7-operating-notes.md`).

For the standalone Opus 4.7 migration kit, see the companion repo at `https://github.com/7alexhale5-rgb/opus-4-7-playbook`.

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
