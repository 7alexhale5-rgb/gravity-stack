# The Gravity Stack

> **The complete blueprint for a top 1% AI-native development environment.**

By Alex Hale & Claude | MIT License | 2026

---

## What Is This?

The Gravity Stack documents a production AI-native development environment built on Claude Code. It includes:

- **31 plugins** — Curated, verified, categorized by priority
- **9+3 MCP servers** — Browser automation, web scraping, search, memory, knowledge bases
- **7 lifecycle hooks** — Commit gates, file guards, auto-lint, context injection
- **53 skills** — Reusable prompt templates across 14 categories
- **CARL engine** — 1,073-line governance engine with context brackets, domain rules, and planning router
- **5 agent roles** — Architect, Implementer, Researcher, Reviewer, Tester

Every tool is **verified and running in production**. Every version **pinned and tested**. Every configuration **the actual config** — not a sanitized example.

## Quick Start

### Automated Setup

```bash
git clone https://github.com/alexhale/gravity-stack.git
cd gravity-stack/toolkit
chmod +x install.sh
./install.sh
```

The installer is idempotent — safe to re-run any time.

### Documentation Site

```bash
cd gravity-stack/site
npm install
npm run dev
```

Visit `http://localhost:3000` to browse the full documentation.

## Project Structure

```
gravity-stack/
├── site/                       # Next.js 16 documentation site
│   ├── src/
│   │   ├── app/                # 11 page routes
│   │   ├── components/         # UI component library
│   │   └── lib/data/           # Typed data layer
│   └── package.json
├── toolkit/                    # Automated setup scripts
│   ├── install.sh              # Master bootstrap
│   ├── scripts/                # 5 phase scripts
│   ├── configs/                # Template settings + commit gate
│   └── templates/              # CLAUDE.md template
├── docs/                       # Deep-dive documentation
│   ├── plugins.md
│   ├── mcp-servers.md
│   ├── hooks.md
│   ├── carl.md
│   ├── skills.md
│   ├── design-system.md
│   └── troubleshooting.md
├── CLAUDE.md                   # Project context
├── LICENSE                     # MIT
└── README.md                   # You are here
```

## Documentation

| Page | Description |
|------|-------------|
| [Manifesto](/site) | Why AI-native development matters |
| [Stack](/site) | Architecture overview — 3 layers |
| [Plugins](/site) | All 31 plugins with categories and priorities |
| [MCP Servers](/site) | Server configs and setup guides |
| [Hooks](/site) | 7 lifecycle hooks with code |
| [CARL](/site) | Governance engine deep-dive |
| [Agents](/site) | Team configuration and usage |
| [Architecture](/site) | Full system diagram |
| [Setup](/site) | Step-by-step installation |
| [Roadmap](/site) | What's planned next |

## Tech Stack

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

1. Fork the repo
2. Create a feature branch
3. Make your changes
4. Run `cd site && npm run build` — must produce zero errors
5. Open a PR

## License

MIT License — see [LICENSE](LICENSE) for details.

---

*Built by humans and AI, working together.*
