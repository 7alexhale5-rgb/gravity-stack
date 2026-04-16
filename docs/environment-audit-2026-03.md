# Gravity Stack — Full Environment Audit
> **Generated:** 2026-03-27 | **By:** the author & Claude
> **Purpose:** Complete map of AI-native development environment for peer comparison

---

## Executive Summary

| Component | Documented (Mar 9) | Actual (Mar 27) | Delta |
|-----------|-------------------|-----------------|-------|
| **Plugins** | 31 | 35 | +4 (custom marketplace) |
| **MCP Servers** | 7+3 | 8+3 | +1 (Mission Control) |
| **Hooks** | 7 | 13 | +6 (4D senses, block-destructive, auto-vision, auto-instinct) |
| **Skills** | 53 | 60+ custom + 100+ plugin-provided | Massive expansion |
| **CARL Domains** | 3 mentioned | 5 active + 1 template | +2 |
| **CARL Rules** | ~13 | 100+ (across 5 domains + 3 context brackets + 8 star-commands) | Massive expansion |
| **Agents** | 5 roles | 11 specialized | +6 |
| **Scripts** | 5 toolkit | 5 toolkit + 4 perception + 1 utility | +5 |
| **Scheduled Jobs** | 0 | 4+ launchd agents | +4 |
| **New Systems** | 0 | 4D Senses, Media Pipeline, Web Escalation, Two-Tier Memory | 4 major systems |

---

## 1. Plugins (35 Total)

### Official Marketplace (30)
| # | Plugin | Category | Priority |
|---|--------|----------|----------|
| 1 | `everything-claude-code` | core | essential |
| 2 | `feature-dev` | development | essential |
| 3 | `context7` | research | essential |
| 4 | `frontend-design` | design | essential |
| 5 | `code-review` | review | essential |
| 6 | `superpowers` | core | essential |
| 7 | `github` | integration | essential |
| 8 | `ralph-loop` | development | recommended |
| 9 | `code-simplifier` | review | recommended |
| 10 | `typescript-lsp` | development | essential |
| 11 | `playwright` | testing | recommended |
| 12 | `commit-commands` | development | essential |
| 13 | `security-guidance` | review | recommended |
| 14 | `serena` | development | recommended |
| 15 | `pr-review-toolkit` | review | recommended |
| 16 | `claude-md-management` | development | recommended |
| 17 | `figma` | design | optional |
| 18 | `pyright-lsp` | development | optional |
| 19 | `supabase` | deployment | optional |
| 20 | `agent-sdk-dev` | development | optional |
| 21 | `atlassian` | integration | optional |
| 22 | `claude-code-setup` | core | optional |
| 23 | `vercel` | deployment | recommended |
| 24 | `learning-output-style` | core | optional |
| 25 | `slack` | integration | optional |
| 26 | `coderabbit` | review | optional |
| 27 | `pinecone` | integration | optional |
| 28 | `firecrawl` | research | recommended |
| 29 | `skill-creator` | core | recommended |
| 30 | `qodo-skills` | testing | optional |

### Custom Marketplace (5)
| # | Plugin | Source | Purpose |
|---|--------|--------|---------|
| 31 | `prettyfly` | `prettyfly-ai` | PrettyFly-specific workflows and conventions |
| 32 | `shiploop` | `7alexhale5-rgb/shiploop` | Dev lifecycle orchestration plugin |
| 33 | `autoresearch` | `uditgoenka/autoresearch` | Research automation |
| 34 | `ui-ux-pro-max` | `nextlevelbuilder/ui-ux-pro-max-skill` | Advanced UI/UX design intelligence |
| 35 | `interface-design` | `Dammyjay93/interface-design` | Dashboard/app interface design |

### Custom Plugin Sources (3 registries)
```json
"extraKnownMarketplaces": {
  "everything-claude-code": "everything-claude-code",
  "prettyfly-ai": "prettyfly-ai",
  "7alexhale5-rgb/shiploop": "7alexhale5-rgb/shiploop"
}
```

---

## 2. MCP Servers (8 Local + 3 Cloud = 11 Total)

### Local Servers
| Server | Type | Package/URL | Purpose |
|--------|------|-------------|---------|
| **Playwright** | npm | `@playwright/mcp@0.0.68` | Browser automation, E2E testing |
| **Firecrawl** | npm | `firecrawl-mcp@3.9.0` | AI web extraction, markdown output |
| **Perplexity** | npm | `@perplexity-ai/mcp-server@0.8.2` | Web search, real-time answers |
| **Memory** | npm | `@modelcontextprotocol/server-memory@2026.1.26` | Session knowledge graph → `~/.claude/memory/graph.json` |
| **Hacker News** | npm | `hn-mcp@1.0.0` | HN stories, search, analysis |
| **Obsidian** | SSE | `http://localhost:22360/sse` | Vault navigation, note CRUD |
| **Crawl4AI** | SSE | `http://localhost:11235/mcp/sse` | Advanced web crawling |
| **Custom MCP (ops)** | node | `your-ops-mcp/mcp-server.js` | Example: org-internal agent coordination over a VPS bridge |

### Cloud Services (Native MCP)
| Service | Tools Prefix | Purpose |
|---------|-------------|---------|
| **Gmail** | `mcp__claude_ai_Gmail__` | Email read/draft/search |
| **Google Calendar** | `mcp__claude_ai_Google_Calendar__` | Event CRUD, free time |
| **Slack** | `mcp__claude_ai_Slack__` | Channel read, message, search |

### Plugin-Provided MCP (via marketplace plugins)
| Plugin | MCP Tools | Purpose |
|--------|-----------|---------|
| **Pencil** | `mcp__pencil__*` | .pen file design editor |
| **Serena** | `mcp__plugin_serena_serena__*` | Semantic code navigation |
| **Context7** | `mcp__plugin_context7_context7__*` | Library documentation lookup |
| **Pinecone** | `mcp__plugin_pinecone_pinecone__*` | Vector database operations |
| **ScreenMind** | `mcp__screenmind__*` | Screen recording analysis |

---

## 3. Hooks (13 Total)

### Documented Original (7)
| # | Name | Event | Matcher | Purpose |
|---|------|-------|---------|---------|
| 1 | **Notification** | Notification | — | macOS notification when Claude needs input |
| 2 | **Session Backup** | PreCompact | — | Saves transcript before context compaction |
| 3 | **File Guard** | PreToolUse | Edit\|Write | Blocks edits to `.env`, `package-lock.json`, `.git/`, `migrations/` |
| 4 | **Commit Gate** | PreToolUse | Bash | Blocks commits with TypeScript errors (`commit-gate.py`) |
| 5 | **Auto-Lint** | PostToolUse | Edit\|Write | TypeScript + ESLint checks on file edits |
| 6 | **Session Context** | SessionStart | — | Injects git status, CLAUDE.md, open issues |
| 7 | **CARL Injection** | UserPromptSubmit | — | Dynamic rule injection via `carl-hook.py` |

### NEW Since March 9 (6)
| # | Name | Event | Matcher | File | Purpose |
|---|------|-------|---------|------|---------|
| 8 | **Block Destructive** | PreToolUse | Bash | `block-destructive.sh` | Prevents `rm -rf`, `git push --force` to main, `DROP TABLE`, `git reset --hard` |
| 9 | **Sense 8: Smell** | PostToolUse | Edit\|Write | `sense-8-smell.js` | Detects god files (>500 LOC), deep nesting (>6), duplication, hardcoded secrets, console.log pollution, TODO accumulation. Severity: GREEN→YELLOW→RED |
| 10 | **Sense 10: Pain** | PostToolUse | Edit\|Write\|Bash | `sense-10-pain.js` | Tracks segfaults, OOM, syntax errors, test failures. Maintains `pain-log.json`. Escalates on 3+ same type in 5min. Session pause alert at 5+ events in 30min |
| 11 | **Sense 15: Intuition** | PostToolUse | Edit\|Write\|Bash | `sense-15-intuition.js` | Reads feedback memory files, matches against past mistakes. Time-based alerts (1-5AM critical edits). Confidence: HIGH/MEDIUM/LOW |
| 12 | **4D Auto-Vision** | UserPromptSubmit | — | `4d-auto-vision.py` | Auto-detects video URLs (YouTube, IG, TikTok, X, Loom), launches `watch-video.py`. Max 2 URLs/message, 120s timeout |
| 13 | **Auto-Instinct** | SessionStart | — | `auto-instinct.sh` | Observes session patterns for continuous learning |

### Sensory Memory System
```
~/.claude/sensory-memory/
├── pain-log.json              # Pain event log (timestamp/type/severity/tool)
├── pain-checkpoints.log       # Critical file edit record
├── pain-session-alert          # Session alert debounce file
├── sense-15-debounce.json     # Intuition warning debounce tracker
└── /tmp/sense15-lessons-cache.json  # Feedback lesson cache (60s TTL)
```

---

## 4. CARL Governance Engine (5 Domains, 21+ Rules)

### Manifest Configuration
| Domain | State | Always On | Recall Keywords |
|--------|-------|-----------|-----------------|
| **GLOBAL** | active | YES | — (every prompt) |
| **CONTEXT** | active | YES | — (every prompt) |
| **COMMANDS** | active | NO | `*dev`, `*review`, `*brief` (star-commands) |
| **ROUTING** | active | NO | `model`, `agent`, `task`, `spawn`, `haiku`, `sonnet`, `opus`, `routing` |
| **EXECUTION** | active | NO | `implement`, `build`, `execute`, `coding`, `build-stack`, `verify`, `review`, `review-stack`, `ready to ship` |

### GLOBAL Rules (13 rules — always loaded)
| # | Rule | Category |
|---|------|----------|
| 0 | Meta: GLOBAL rules apply universally | Meta |
| 1 | Use absolute paths in all programming | Filesystem |
| 2 | Use relative paths when referencing files to user | UX |
| 3 | Batch tool calls when possible | Performance |
| 4 | NEVER mark tasks complete without validating functionality | Quality |
| 5 | Read files before editing them | Process |
| 6 | Prefer editing existing files over creating new ones | Process |
| 7 | Keep changes minimal and focused | Scope Control |
| 8 | Avoid over-engineering | Scope Control |
| 9 | PLANNING ROUTER: Non-trivial tasks → `/planning-stack` | Planning |
| 10 | PLANNING ROUTER: Trivial tasks (<10 LOC) skip planning | Planning |
| 11 | PLANNING ROUTER: Context depleted → `/plan` (subagent isolation) | Planning |
| 12 | PLANNING ROUTER: If `.planning/` exists, suggest phase-aware commands | Planning |

### CONTEXT Rules (Context Bracket System)
- **FRESH** (>60% context): Lean injection, minimal overhead, aggressive batching
- **MODERATE** (40-60%): Standard injection, normal overhead
- **DEPLETED** (<40%): Subagent isolation, context-preserving strategies

### ROUTING Rules (On-demand)
- Model selection guidance for Task/agent spawning
- Haiku for fast/cheap (scout, quickfix), Sonnet for balanced, Opus for thorough/production

### EXECUTION Rules (On-demand)
- Build-phase workflow routing after planning completes
- Links to `/build-stack`, `/review-stack`, `/ship`

### COMMANDS Rules (On-demand)
- Star-command routing (`*dev`, `*review`, `*brief`)

---

## 5. Agent System (11 Specialized Agents)

### Agent Roster
| Agent | Model | Speed/Cost | Invocation | Purpose | Tools |
|-------|-------|-----------|------------|---------|-------|
| `scout` | Haiku 4.5 | Fast/Cheap | `Task(scout)` | Quick file searches, pattern matching | Read, Glob, Grep |
| `quickfix` | Haiku 4.5 | Fast/Cheap | `Task(quickfix)` | Small fixes, typos, version bumps | Read, Glob, Grep, Edit |
| `research` | Opus | Thorough | `Task(research)` | Deep investigation, codebase exploration | Read, Glob, Grep, WebSearch, WebFetch |
| `architect` | Opus | Thorough | `Task(architect)` | System design, integration planning | Read, Glob, Grep, Write, Edit |
| `implementer` | Opus | Thorough | `Task(implementer)` | Code writing with minimal overhead | Read, Glob, Grep, Write, Edit, Bash |
| `tester` | Opus | Thorough | `Task(tester)` | Test coverage, QA, verification | Read, Glob, Grep, Write, Edit, Bash |
| `reviewer` | Opus | Thorough | `Task(reviewer)` | Code review, security audit | Read, Glob, Grep |
| `supabase` | Opus | Thorough | `Task(supabase)` | Database, pgvector, edge functions | Read, Glob, Grep, Write, Edit, Bash, MCP |
| `jr-dev-executor` | Opus | Thorough | `Task(jr-dev-executor)` | Pipeline build from Mike's handoff artifacts | Read, Write, Edit, Bash, Grep, Glob, Task |
| `stakeholder-reviewer` | Sonnet | Balanced | `Task(stakeholder-reviewer)` | Multi-perspective document review | Read, Grep, Glob |
| `custom-telegram` | Haiku 4.5 | Autonomous | `@your_telegram_bot` | Example: autonomous Telegram assistant via a Claw-style runtime | Custom tools |

### Experimental Flags
```json
{ "env": { "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1" } }
```

---

## 6. Skills (60+ Custom + 100+ Plugin-Provided)

### Custom Skills (45 in `~/.claude/skills/`)

#### Planning & Strategy (7)
| Skill | Command | Description |
|-------|---------|-------------|
| Planning Stack | `/planning-stack` | Multi-source planning pipeline with `--shallow`, `--deep`, `--tech` flags |
| Brainstorm Stack | `/brainstorm-stack` | Adaptive pre-planning questioning to gather context |
| Research Stack | `/research-stack` | Multi-phase research combining web, docs, codebase analysis |
| Dispatch | `/dispatch` | Context-aware router for the skill ecosystem |
| Devil's Advocate | `/devilsadvocate` | Deep verification of research claims and assumptions |
| Defuddle | `/defuddle` | Extract clean markdown from web pages (token-efficient) |
| Drift | `/drift` | Check if current work aligns with weekly focus |

#### Build & Implementation (5)
| Skill | Command | Description |
|-------|---------|-------------|
| Build Stack | `/build-stack` | Build-phase orchestrator with verification checkpoints + subagent integration |
| Review Stack | `/review-stack` | 4-layer quality gate (static→pattern→contextual→runtime) with remediation reports |
| Ship | `/ship` | One-command release flow (sync→test→push→PR) |
| Verify Phase | `/verify-phase` | AI-reviewed phase verification against acceptance criteria |
| Next Phase | `/next-phase` | Mark phase complete, advance in ROADMAP.md |

#### Project Management (5)
| Skill | Command | Description |
|-------|---------|-------------|
| Init Project | `/init-project` | Create `.planning/` with PROJECT.md and ROADMAP.md |
| Plan Phase | `/plan-phase` | Detail specific phase with files to modify and test criteria |
| Project Progress | `/project-progress` | Dashboard showing phase statuses and completion % |
| Project Registry | `/project-registry` | Index of all active projects with locations and status |
| Project Connect | `/project-connect` | Link codebase to vault project notes |

#### Session & State (6)
| Skill | Command | Description |
|-------|---------|-------------|
| Pause Work | `/pause-work` | Save session state to `.planning/STATE.md` |
| Resume Work | `/resume-work` | Restore project from saved state with 30s briefing |
| Handoff | `/handoff` | Full session persist + handoff doc + resume prompt |
| Close Day | `/close-day` | End-of-day capture with memory sync |
| Morning Brief | `/morning-brief` | Start-of-day digest from vault + suggested first move |
| Focus Update | `/focus-update` | Weekly 6-question interview → `current-focus.md` |

#### Code & Development (4)
| Skill | Command | Description |
|-------|---------|-------------|
| Supabase Patterns | `/supabase-patterns` | Production Supabase for Next.js/TypeScript |
| Prompt Engineering | `/prompt-engineering` | Production-ready prompt design with cost awareness |
| Codebase-to-Course | `/codebase-to-course` | Transform codebase into interactive HTML course |
| Jr Dev | `/jr-dev` | Pipeline-driven builds from upstream artifacts |

#### Design & UI (1)
| Skill | Command | Description |
|-------|---------|-------------|
| UA/UX | `/ua-ux` | Design system overlay orchestrating 3 design plugins |

#### Research & Information (3)
| Skill | Command | Description |
|-------|---------|-------------|
| Vault Search | `/vault-search` | 3-layer search across T2 memory vault |
| Vault Context | `/vault-context` | Load personal context from Obsidian into session |
| Trace | `/trace` | Surface decision history from memory vault |

#### Obsidian Integration (4)
| Skill | Command | Description |
|-------|---------|-------------|
| Obsidian CLI | `/obsidian-cli` | Vault CRUD via CLI |
| Obsidian Markdown | `/obsidian-markdown` | Obsidian Flavored Markdown (wikilinks, callouts) |
| Obsidian Bases | `/obsidian-bases` | Database-like views (.base files) |
| JSON Canvas | `/json-canvas` | Visual thinking canvases (.canvas files) |

#### Writing & Documentation (3)
| Skill | Command | Description |
|-------|---------|-------------|
| Writing Skills | `/writing-skills` | Skill authoring guide |
| Voice Check | `/voice-check` | Review content against established voice |
| Compound | `/compound` | Engineering retrospective + learning documentation |

#### Business & Operations (3)
| Skill | Command | Description |
|-------|---------|-------------|
| Ideas | `/ideas` | Capture product/feature ideas with 3-question interview |
| Gig Generator | `/gig-generator` | Platform-ready gig listings from strategy matrix |
| Proposal Generator | `/proposal-generator` | Custom proposals from job postings |

#### Governance & Monitoring (3)
| Skill | Command | Description |
|-------|---------|-------------|
| Cost Management | `/cost-management` | API budget monitoring with thresholds |
| CARL Manager | `/carl-manager` | Manage CARL domains and rules conversationally |
| Watch Recording | `/watch-recording` | Process screen recordings via ScreenMind |

### Plugin-Provided Skills (100+ from marketplace plugins)

Major plugin skill families:
- **everything-claude-code**: `/plan`, `/tdd`, `/code-review`, `/e2e`, `/learn-eval`, `/claw`, `/article-writing`, `/frontend-slides`, `/investor-materials`, `/market-research`, `/content-engine`, and 40+ more
- **superpowers**: `/brainstorming`, `/writing-plans`, `/executing-plans`, `/systematic-debugging`, `/test-driven-development`, `/verification-before-completion`, `/dispatching-parallel-agents`, `/subagent-driven-development`, `/using-git-worktrees`
- **vercel**: `/nextjs`, `/ai-sdk`, `/ai-gateway`, `/shadcn`, `/workflow`, `/vercel-cli`, `/vercel-functions`, `/ai-elements`, `/chat-sdk`, and 30+ more
- **figma**: `/figma-use`, `/figma-implement-design`, `/figma-generate-design`, `/figma-generate-library`, `/figma-create-design-system-rules`, `/figma-code-connect-components`
- **pinecone**: `/quickstart`, `/query`, `/assistant`, `/cli`, `/docs`, `/mcp`
- **firecrawl**: `/firecrawl-cli`, `/skill-gen`
- **coderabbit**: `/code-review`
- **atlassian**: `/capture-tasks-from-meeting-notes`, `/generate-status-report`, `/spec-to-backlog`, `/search-company-knowledge`, `/triage-issue`
- **interface-design**: `/init`, `/audit`, `/critique`, `/extract`, `/status`
- **GSD** (Get Stuff Done): `/gsd:progress`, `/gsd:plan-phase`, `/gsd:execute-phase`, `/gsd:new-project`, `/gsd:new-milestone`, `/gsd:resume-work`, `/gsd:pause-work`, `/gsd:debug`, and 15+ more

---

## 7. Two-Tier Memory System

### Architecture
| Tier | Engine | Location | Scope | Auto-Load |
|------|--------|----------|-------|-----------|
| **T1: Hot Context** | Auto-memory | `~/.claude/projects/*/memory/` | Per-project | 200 lines of MEMORY.md |
| **T2: Persistent** | Obsidian vault | `~/vault/` | Cross-project, cross-session | Manual (Grep → Read) |
| **Session Graph** | MCP Memory | `~/.claude/memory/graph.json` | Single session | Via memory MCP server |

### T2 Vault Structure
```
~/vault/
├── sessions/          # Session summaries
├── handoffs/          # Cross-session handoff docs
├── planning/          # Plans and architecture decisions
├── decisions/         # Key decision records
├── brainstorms/       # Brainstorm outputs
├── costs/             # Cost tracking
├── ideas/             # Idea captures
└── focus/             # Weekly focus files
```

### Memory Operations
- **T1 Write**: Auto-memory files at `~/.claude/projects/{project}/memory/`
- **T2 Write**: `Write` tool → `~/vault/{folder}/{date}-{slug}.md` with YAML frontmatter
- **T2 Search**: `Grep` pattern on vault path → `Read` matched files
- **Graph**: `mcp__memory__*` tools for session-scoped entity relationships

---

## 8. Media Processing Pipeline (4D Vision)

### Auto-Detection (UserPromptSubmit hook)
Video URLs in messages are automatically detected and processed:
- YouTube, Instagram Reels, TikTok, X/Twitter, Loom, direct MP4/MOV/WEBM
- Max 2 URLs per message, 120s timeout
- Output: `/tmp/video-intelligence/<video_id>/`

### Scripts
| Script | Purpose | Speed |
|--------|---------|-------|
| `watch-video.py` | Video analysis (3 depth levels: shallow/normal/deep) | 10-60s |
| `transcribe-gemini.py` | Audio/video transcription via Gemini 2.5 Flash | ~60s/hr of audio |
| `diarize-audio.py` | Speaker diarization (WhisperX + pyannote) | Varies |
| `stealth-fetch.py` | Anti-bot web scraping (Scrapling, Tier 2.5) | 1-5s |

### Web Escalation Chain
| Tier | Tool | When |
|------|------|------|
| 0 | WebFetch | Static pages |
| 1 | Firecrawl MCP | Default — AI extraction |
| 2 | defuddle | Clean markdown, fewer tokens |
| **2.5** | **stealth-fetch.py** | Cloudflare-protected, anti-bot |
| 3 | Playwright MCP | JS-rendered, interaction needed |
| 4 | WebSearch | Find cached/mirrored version |

### Required API Keys
| Key | Location | Purpose |
|-----|----------|---------|
| `GEMINI_API_KEY` | `~/.claude/secrets/gemini.env` | Video perception, transcription |
| `GROQ_API_KEY` | `~/.claude/secrets/groq.env` | Audio transcription fallback |
| `HF_TOKEN` | `~/.claude/secrets/huggingface.env` | Speaker diarization |

---

## 9. Reference Documents

| File | Location | Purpose |
|------|----------|---------|
| `media-routing.md` | `~/.claude/references/` | Complete media processing decision tree |
| `AGENTS.md` | `~/.claude/` | Agent definitions and invocation patterns |
| `keybindings.json` | `~/.claude/` | Custom keyboard shortcuts |

---

## 10. Scheduled Jobs (launchd)

| Job | Schedule | Purpose |
|-----|----------|---------|
| `com.prettyfly.marketing-queue` | Every 5 min | Marketing queue runner |
| `com.prettyfly.marketing-token-refresh` | Sun 3 AM | Token refresh |
| `com.prettyfly.gig-monitor` | Daily 6:45 AM | Gig monitoring |
| `com.prettyfly.gig-watchdog` | Daily 7:45 AM | Gig watchdog |
| `com.prettyfly.downloads-cleanup` | 1st of month, 9 AM | Downloads folder cleanup reminder |

---

## 11. Toolkit Scripts

### Core Toolkit (`gravity-stack/toolkit/`)
| Script | Purpose |
|--------|---------|
| `install.sh` | Master installer (orchestrates all scripts) |
| `scripts/01-foundation.sh` | Node.js, Python, Homebrew, core CLIs |
| `scripts/02-claude-code.sh` | Claude Code CLI, settings, plugins |
| `scripts/03-mcp-servers.sh` | MCP server installation and config |
| `scripts/04-hooks.sh` | Hook installation |
| `scripts/05-verify.sh` | Verification suite |
| `configs/settings.json` | Template settings.json |
| `configs/commit-gate.py` | TypeScript commit gate hook |
| `templates/CLAUDE.md.template` | Project CLAUDE.md template |
| `vault-search.sh` | T2 vault search utility |

### NOT in Toolkit (should be added)
| Script | Location | Purpose |
|--------|----------|---------|
| `sense-8-smell.js` | `~/.claude/hooks/` | Code smell detector |
| `sense-10-pain.js` | `~/.claude/hooks/` | Pain/failure detector |
| `sense-15-intuition.js` | `~/.claude/hooks/` | Pattern matching against past feedback |
| `4d-auto-vision.py` | `~/.claude/hooks/` | Auto video URL detection |
| `auto-instinct.sh` | `~/.claude/hooks/` | Session learning observer |
| `block-destructive.sh` | `~/.claude/hooks/` | Destructive command blocker |
| `watch-video.py` | `~/.claude/scripts/` | Video analysis pipeline |
| `transcribe-gemini.py` | `~/.claude/scripts/` | Gemini transcription |
| `diarize-audio.py` | `~/.claude/scripts/` | Speaker diarization |
| `stealth-fetch.py` | `~/.claude/scripts/` | Anti-bot web scraping |
| `carl-hook.py` | `~/.claude/hooks/` | CARL context injection |
| `AGENTS.md` | `~/.claude/` | Agent definitions |
| `~/.carl/*` | `~/.carl/` | CARL domain files |

---

## 12. Site Staleness Report

### Pages with Stale Counts
| Page | Claims | Reality | Fix |
|------|--------|---------|-----|
| Homepage | 53 Skills | 60+ custom | Update to current count |
| Stack | 53 Skills | 60+ custom | Update to current count |
| Skills | 53 skills across 14 categories | 60+ across 14 categories | Update metadata + add new skills |
| Architecture | 53 Skills in diagram | 60+ custom | Update diagram text |

### Pages Missing Entirely
| Topic | Status | Priority |
|-------|--------|----------|
| 4D Senses / Perception System | NOT documented | HIGH |
| Media Processing Pipeline | NOT documented | HIGH |
| Two-Tier Memory System | NOT documented | HIGH |
| Web Escalation Chain | NOT documented | MEDIUM |
| Scheduled Jobs | NOT documented | LOW |
| API Keys / Secrets Management | NOT documented | MEDIUM |

### Data Files Needing Updates
| File | Current | Needed |
|------|---------|--------|
| `plugins.ts` | 31 entries | Add 4 custom plugins (prettyfly, shiploop, autoresearch, ui-ux-pro-max, interface-design) |
| `mcp-servers.ts` | 7+3 entries | Add Mission Control server |
| `hooks.ts` | 7 entries | Add 6 new hooks (block-destructive, sense-8, sense-10, sense-15, 4d-auto-vision, auto-instinct) |
| `skills.ts` | 60 entries | Verify all 45 custom skills present, add missing |
| `stack.ts` | 5 agent roles | Update to 11 agents |

---

## 13. Environment Configuration Summary

### File Locations
```
~/.claude/
├── settings.json              # Main config (plugins, MCP servers, hooks, env vars, permissions)
├── settings.local.json        # Local overrides
├── AGENTS.md                  # Agent definitions
├── CLAUDE.md                  # Global instructions
├── keybindings.json           # Custom keyboard shortcuts
├── memory/
│   └── graph.json             # Session knowledge graph
├── sensory-memory/            # 4D Senses state
│   ├── pain-log.json
│   ├── pain-checkpoints.log
│   └── sense-15-debounce.json
├── secrets/                   # API keys (gitignored)
│   ├── gemini.env
│   ├── groq.env
│   └── huggingface.env
├── hooks/                     # Hook scripts
│   ├── block-destructive.sh
│   ├── sense-8-smell.js
│   ├── sense-10-pain.js
│   ├── sense-15-intuition.js
│   ├── 4d-auto-vision.py
│   └── auto-instinct.sh
├── scripts/                   # Utility scripts
│   ├── watch-video.py
│   ├── transcribe-gemini.py
│   ├── diarize-audio.py
│   └── stealth-fetch.py
├── references/                # Reference documents
│   └── media-routing.md
├── skills/                    # 45 custom skills
│   └── {skill-name}/SKILL.md
└── projects/                  # Per-project memory (T1)
    └── {project}/memory/

~/.carl/                       # CARL governance engine
├── manifest                   # Domain state and recall keywords
├── global                     # Always-on rules (13)
├── context                    # Context bracket rules
├── commands                   # Star-command routing
├── routing                    # Model/agent selection
├── execution                  # Build-phase workflow routing
├── example-custom-domain      # Template for new domains
└── sessions/                  # Session state tracking

~/vault/       # T2 persistent memory (Obsidian)
├── sessions/
├── handoffs/
├── planning/
├── decisions/
├── brainstorms/
└── focus/
```

---

---

## 14. CARL Deep Dive (100+ Rules Across 5 Domains)

### How CARL Works (4-Step Loop)
1. **User submits prompt** → Triggers `UserPromptSubmit` hook
2. **carl-hook.py evaluates manifest** → Determines which domains to load
3. **Rules inject into system context** → Becomes implicit guidance
4. **Claude responds** → Following injected rules automatically

### Manifest (`~/.carl/manifest`)
```
DEVMODE=false

GLOBAL_STATE=active    GLOBAL_ALWAYS_ON=true
CONTEXT_STATE=active   CONTEXT_ALWAYS_ON=true
COMMANDS_STATE=active  COMMANDS_ALWAYS_ON=false
ROUTING_STATE=active   ROUTING_ALWAYS_ON=false   ROUTING_RECALL=model,agent,task,spawn,haiku,sonnet,opus,routing
EXECUTION_STATE=active EXECUTION_ALWAYS_ON=false  EXECUTION_RECALL=implement,build,execute,coding,build-stack,verify,review,review-stack,ready to ship
```

### Domain: GLOBAL (13 rules — always loaded)
Foundational behaviors: absolute paths, batch tool calls, read-before-edit, minimal changes, no over-engineering, multi-tier planning router (trivial→shallow→default→deep→subagent isolation).

### Domain: CONTEXT (16 rules — always loaded, bracket-adaptive)
| Bracket | Context Remaining | Behavior |
|---------|------------------|----------|
| **FRESH** | 60-100% | Lean injection, aggressive batching, work in current context |
| **MODERATE** | 40-60% | Re-state goals, re-read requirements, consider agent spawning at 300+ LOC |
| **DEPLETED** | 15-40% | Checkpoint progress, suggest `/handoff`, force `/plan` subagent isolation |
| **CRITICAL** | <15% | Block complex planning, force handoff |

### Domain: COMMANDS (8 star-commands, 43 rules — keyword-triggered)
| Command | Rules | Purpose |
|---------|-------|---------|
| `*dev` | 5 | Code over explanation, minimal changes |
| `*review` | 5 | Full context, flag security, note performance |
| `*brief` | 4 | Bullet points only, max 5 items |
| `*plan` | 5 | Explore first, present options, get approval |
| `*discuss` | 5 | Multiple approaches, clarifying questions |
| `*debug` | 5 | Gather context, hypothesis-driven, root cause |
| `*explain` | 5 | High-level first, concrete examples, incremental |
| `*carl` | 9 | CARL help mode, system administration |

### Domain: ROUTING (6 rules — triggered by model/agent keywords)
| Model | Use Case | Cost |
|-------|----------|------|
| **Haiku** | Scout, quickfix, grep/glob, background agents | 1x baseline |
| **Sonnet** | Feature coding, review, testing, research | 3-5x |
| **Opus** | Architecture, deep planning, security, multi-file | 10x+ |

Default: Sonnet. Escalate to Opus only for cross-system impact.

### Domain: EXECUTION (8 rules — triggered by build/implement keywords)
Complete workflow chain:
```
/planning-stack → /build-stack → /review-stack → /simplify → /commit → /ship → /compound
```
Auto-handoff at DEPLETED bracket. Library-first philosophy (anti-NIH via `ecc:search-first`).

---

## 15. Hook Execution Order (Complete Architecture)

### UserPromptSubmit (fires on every message)
1. `carl-hook.py` — CARL context injection (domain rules based on keywords)
2. `4d-auto-vision.py` — Auto-detect video URLs, launch `watch-video.py`

### SessionStart (fires on session init)
1. Session Context script — git status, CLAUDE.md, open issues
2. Usage Reminder — cost tracking display
3. `auto-instinct.sh` — Continuous learning observer trigger (non-blocking Haiku)

### PreToolUse: Edit|Write
1. File Guard — blocks `.env`, `package-lock.json`, `.git/`, `migrations/`

### PreToolUse: Bash
1. `block-destructive.sh` — prevents `rm -rf`, `git push --force` to main, `DROP TABLE`, `git reset --hard`, `git clean -f`
2. `commit-gate.py` — blocks commits with TypeScript errors

### PostToolUse: Edit|Write
1. Auto-Lint — TypeScript + ESLint checks
2. `sense-8-smell.js` — God files, deep nesting, duplication, secrets, console pollution, TODO accumulation

### PostToolUse: Edit|Write|Bash
1. `sense-10-pain.js` — Segfaults, OOM, syntax errors, test failures. Escalates on 3+ same type in 5min
2. `sense-15-intuition.js` — Pattern-matches against feedback memory files, pain history, risky operations, late-night edits

### PreCompact
1. Session Backup — saves transcript to T2 vault before compaction

### Notification
1. macOS notification when Claude needs input

---

## 16. Perspectives Engine (9 Review Lenses)

Located in `~/.claude/skills/_perspectives/` — used by `/review-stack`:

| Perspective | Focus |
|-------------|-------|
| `accessibility.md` | WCAG compliance, screen readers, keyboard nav |
| `architecture.md` | Separation of concerns, modularity, scalability |
| `code-quality.md` | Readability, maintainability, conventions |
| `lighthouse.md` | Performance scores, Core Web Vitals |
| `performance.md` | Runtime efficiency, memory, network |
| `security.md` | OWASP Top 10, auth, injection, secrets |
| `test-coverage.md` | Unit, integration, E2E coverage gaps |
| `skeptic.md` | Devil's advocate at every pipeline step |

---

*This audit reflects the complete state of Alex Hale's Claude Code environment as of March 27, 2026. Every component has been verified against live configuration files by 9 parallel audit agents.*
