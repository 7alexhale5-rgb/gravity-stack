# Handoff: Gravity Stack — Build Phase

**Date:** 2026-03-09
**Status:** Planning complete, ready for implementation
**Project:** ~/Projects/gravity-stack/

## What Was Done

The Gravity Stack implementation guide ("The Bible") is complete at `.planning/IMPLEMENTATION-GUIDE.md` — 1,200+ lines, 24 chapters, 6 parts, 6 appendices. Every technical claim has been validated against live sources.

### Key Verified Facts
- **Next.js 16.1.6** (NOT 15) — use `npx create-next-app@latest . --yes`
- **Tailwind v4.2** — CSS-based config with `@theme` blocks, NO `tailwind.config.ts`
- **Satoshi font** — NOT on Google Fonts, must self-host via `next/font/local` from fontshare.com
- **31 plugins** (NOT 32) — full catalog with exact slugs in Appendix A
- **9+3 MCP servers** — exact JSON configs in Appendix B
- **7 hooks** — full code in Appendix C
- **CARL** — 1,073-line Python governance engine confirmed
- **53 custom skills** — cataloged in Appendix E

### Files Created
- `.planning/IMPLEMENTATION-GUIDE.md` — THE master document (the Bible)
- `.git/` — repo initialized

### Vision (from Alex)
- "The Bible" — comprehensive, exhaustive reference for AI-native dev in 2026
- Ebook-style chapters, NOT flat docs
- Generalized for anyone — no personal/business specifics
- "Give all the juice for free"
- Premium, impressive quality — "sending this to people"
- Attribution: "By Alex Hale & Claude"
- Includes: ALL skills, plugins, workflows, design library, research/planning stacks, ship loop, devil's advocate, UI/UX skills, everything-claude-code deep dive

## What Needs To Be Built Next

### Phase 1: Scaffold (do first)
```bash
cd ~/Projects/gravity-stack/site
npx create-next-app@latest . --yes
npx shadcn@latest init
# Download Satoshi from fontshare.com → src/fonts/
```

### Phase 2: Data Layer
Create typed data modules in `site/src/lib/data/`:
- `plugins.ts` — all 31 plugins (interface + data from Appendix A)
- `mcp-servers.ts` — 9+3 servers (interface + configs from Appendix B)
- `hooks.ts` — 7 hooks (interface + code from Appendix C)
- `stack.ts` — full tool listing
- `skills.ts` — all 53 skills (from Appendix E)

### Phase 3: Components
Build in `site/src/components/`:
Nav, Hero, CodeBlock (with copy-to-clipboard via shiki), Card, Badge, PluginCard, HookCard, Callout, DiagramNode, Timeline

### Phase 4: Pages (11 routes)
/, /manifesto, /stack, /plugins, /mcp-servers, /hooks, /carl, /agents, /architecture, /setup, /roadmap

### Phase 5: Design System
- Fonts: Instrument Serif + DM Mono (next/font/google), Satoshi (next/font/local)
- Colors: @theme block in globals.css (Appendix D)
- Effects: grain overlay, gradient text, card hover glow, sticky nav blur

### Phase 6: Toolkit Scripts
- `toolkit/install.sh` + 5 numbered scripts
- `toolkit/configs/settings.json` template
- `toolkit/configs/commit-gate.py`
- `toolkit/templates/CLAUDE.md.template`

### Phase 7: Documentation
- 7 docs/ markdown files
- Premium README.md
- Project CLAUDE.md

### Phase 8: Verify & Deploy
- `cd site && npm run build` — zero errors
- Deploy to Vercel

## Prompt for Next Session

```
Read .planning/HANDOFF-BUILD-PHASE-20260309.md and .planning/IMPLEMENTATION-GUIDE.md to understand the full project. This is The Gravity Stack — an open-source documentation site + setup toolkit for AI-native development environments. The implementation guide (The Bible) is complete. Now execute it: scaffold the Next.js 16 site, build the data layer, components, all 11 pages, toolkit scripts, and docs. Start with Phase 1 (scaffold) and work through sequentially. The site must build with zero errors and match the design system exactly.
```
