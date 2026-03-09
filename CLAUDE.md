# Gravity Stack

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
