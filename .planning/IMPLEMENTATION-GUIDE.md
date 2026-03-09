# The Gravity Stack — Implementation Guide

> **The complete blueprint for a top 1% AI-native development environment.**
> By Alex Hale & Claude · March 2026

---

## Table of Contents

### Part I — Philosophy
1. [The Manifesto](#chapter-1-the-manifesto)
2. [Why This Stack Exists](#chapter-2-why-this-stack-exists)

### Part II — The Stack
3. [Architecture Overview](#chapter-3-architecture-overview)
4. [Plugin Encyclopedia (31 Plugins)](#chapter-4-plugin-encyclopedia)
5. [MCP Server Constellation (9+3 Servers)](#chapter-5-mcp-server-constellation)
6. [Lifecycle Hooks (7 Hooks)](#chapter-6-lifecycle-hooks)
7. [CARL — Context Augmentation & Reinforcement Layer](#chapter-7-carl)
8. [Agent Teams](#chapter-8-agent-teams)

### Part III — Skills & Workflows
9. [Skills Encyclopedia (53 Skills)](#chapter-9-skills-encyclopedia)
10. [Workflow Playbooks](#chapter-10-workflow-playbooks)
11. [Research Stack](#chapter-11-research-stack)
12. [Planning Stack](#chapter-12-planning-stack)
13. [Ship Loop](#chapter-13-ship-loop)
14. [Devil's Advocate Protocol](#chapter-14-devils-advocate-protocol)

### Part IV — Design & Frontend
15. [Design System](#chapter-15-design-system)
16. [Design Library (6 Systems, 300+ Components)](#chapter-16-design-library)
17. [UI/UX Intelligence](#chapter-17-uiux-intelligence)
18. [Frontend Patterns](#chapter-18-frontend-patterns)

### Part V — Setup & Installation
19. [Prerequisites](#chapter-19-prerequisites)
20. [Automated Setup (Toolkit)](#chapter-20-automated-setup)
21. [Manual Setup Reference](#chapter-21-manual-setup-reference)
22. [Verification & Troubleshooting](#chapter-22-verification)

### Part VI — The Documentation Site
23. [Site Architecture](#chapter-23-site-architecture)
24. [Build & Deploy](#chapter-24-build-and-deploy)

### Appendices
- [A: Verified Plugin Catalog](#appendix-a)
- [B: MCP Server Configurations](#appendix-b)
- [C: Hook Command Reference](#appendix-c)
- [D: Design System Tokens](#appendix-d)
- [E: Skills Quick-Reference](#appendix-e)
- [F: Spec Corrections Log](#appendix-f)

---

# Part I — Philosophy

## Chapter 1: The Manifesto

The AI-native developer doesn't use AI as a copilot. They build **systems** where AI is the primary interface to their entire development environment — code, infrastructure, memory, deployment, communication, and design — all accessible through natural language in a single terminal.

This isn't about typing less. It's about **thinking at a higher altitude**. When your AI agent can read your codebase semantically, recall decisions from six months ago, enforce your team's coding standards automatically, run your tests, deploy your infrastructure, manage your project board, and catch your mistakes before they reach git — you stop being a typist and start being an architect.

The Gravity Stack is the blueprint for building that environment.

**Core principles:**
1. **Convention over configuration** — Sensible defaults that work out of the box, with escape hatches for customization
2. **Idempotent everything** — Every script, every hook, every config is safe to re-run
3. **Memory is architecture** — Persistent semantic memory transforms sessions from stateless to cumulative
4. **Governance scales creativity** — Automated guardrails (hooks, CARL, commit gates) free you to move fast without breaking things
5. **Open by default** — Every piece of this stack is free, documented, and forkable

## Chapter 2: Why This Stack Exists

Most Claude Code setups use 2-3 plugins and zero hooks. That's like buying a Ferrari and driving it in first gear.

The Gravity Stack documents a production environment that ships real software across multiple projects simultaneously. The exact configuration described here maintains 97/100 platform audit scores, enforces TypeScript correctness at commit time, persists semantic memory across sessions, and coordinates specialized AI agent teams for different task types.

**What makes this different from other "awesome lists":**
- Every tool is **verified and running** in production — no theoretical recommendations
- Every version number is **pinned and tested** — no "just install the latest"
- Every configuration is **the actual config** — not a sanitized example
- Every workflow is **documented from real usage** — not hypothetical patterns

---

# Part II — The Stack

## Chapter 3: Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     YOUR TERMINAL                            │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                   CLAUDE CODE CLI                        ││
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐              ││
│  │  │ 31       │  │ 9+3 MCP  │  │ 7        │              ││
│  │  │ Plugins  │  │ Servers  │  │ Hooks    │              ││
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘              ││
│  │       │              │              │                    ││
│  │  ┌────▼──────────────▼──────────────▼─────┐             ││
│  │  │           CARL Engine (1,073 lines)     │             ││
│  │  │   Context Brackets · Domain Rules ·     │             ││
│  │  │   Model Routing · Cost Management       │             ││
│  │  └────────────────┬───────────────────────┘             ││
│  │                   │                                      ││
│  │  ┌────────────────▼───────────────────────┐             ││
│  │  │         Agent Teams (5 Roles)           │             ││
│  │  │  Architect · Implementer · Researcher   │             ││
│  │  │  Reviewer · Tester                      │             ││
│  │  └────────────────────────────────────────┘             ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Memory Layer │  │ Obsidian     │  │ Playwright   │      │
│  │ (Semantic)   │  │ (Knowledge)  │  │ (Browser)    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Firecrawl    │  │ Perplexity   │  │ Hacker News  │      │
│  │ (Scraping)   │  │ (Search)     │  │ (Feed)       │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### The Three Layers

**Layer 1: Intelligence** — Claude Code CLI with 31 plugins providing specialized capabilities (code review, testing, deployment, design, security, etc.)

**Layer 2: Governance** — CARL engine + lifecycle hooks enforce rules, inject context, gate commits, guard files, and route tasks to the right model tier.

**Layer 3: Infrastructure** — MCP servers connect Claude to external systems: persistent memory, knowledge bases, browsers, web scrapers, search engines, and communication platforms.

### Project Structure

```
gravity-stack/
├── site/                       # Next.js 16 documentation site
│   ├── src/
│   │   ├── app/                # App Router pages (11 routes)
│   │   ├── components/         # Reusable UI components
│   │   └── lib/data/           # Typed data modules
│   ├── public/
│   ├── next.config.ts
│   └── package.json
├── toolkit/                    # Automated setup scripts
│   ├── install.sh              # Master bootstrap
│   ├── scripts/                # 5 numbered phase scripts
│   ├── configs/                # Template configurations
│   └── templates/              # Project scaffolds
├── docs/                       # Deep-dive markdown docs
├── CLAUDE.md                   # Project context
├── README.md
└── LICENSE                     # MIT
```

## Chapter 4: Plugin Encyclopedia

### Overview

31 plugins organized into 7 categories. Each plugin extends Claude Code with specialized skills, tools, and workflows.

> **How plugins work:** Plugins are installed via Claude Code's marketplace. Each plugin provides skills (slash commands), agent types, and MCP tool access. They load on-demand — having 31 enabled doesn't slow startup.

### Essential Plugins (Install These First)

| # | Plugin | Slug | What It Does |
|---|--------|------|-------------|
| 1 | **Everything Claude Code** | `everything-claude-code@everything-claude-code` | The meta-plugin. Adds 60+ skills covering TDD, code review, security scanning, Go/Python/Java patterns, strategic compaction, content writing, deployment patterns, and more. This single plugin is the biggest force multiplier in the stack. |
| 2 | **Superpowers** | `superpowers@claude-plugins-official` | Advanced workflows: brainstorming protocol, plan writing, plan execution, git worktrees, parallel agent dispatch, verification loops, code review request/response, systematic debugging. |
| 3 | **Feature Dev** | `feature-dev@claude-plugins-official` | Guided feature development: codebase exploration → architecture design → code review with confidence-based filtering. Three specialized agents (explorer, architect, reviewer). |
| 4 | **Context7** | `context7@claude-plugins-official` | Fetches up-to-date documentation for any library directly into context. Eliminates hallucinated API calls by grounding Claude in real docs. |
| 5 | **TypeScript LSP** | `typescript-lsp@claude-plugins-official` | Language Server Protocol integration for TypeScript. Real-time type checking, go-to-definition, find references — Claude sees what your IDE sees. |

### Development Plugins

| # | Plugin | Slug | What It Does |
|---|--------|------|-------------|
| 6 | **Code Review** | `code-review@claude-plugins-official` | Structured code review with specialized agents for quality, security, and standards compliance. |
| 7 | **PR Review Toolkit** | `pr-review-toolkit@claude-plugins-official` | Multi-agent PR review: code reviewer, code simplifier, comment analyzer, silent failure hunter, test coverage analyzer, type design analyzer. |
| 8 | **Commit Commands** | `commit-commands@claude-plugins-official` | Conventional commit workflow. `/commit` generates well-structured commit messages, `/commit-push-pr` goes from commit to PR in one command. |
| 9 | **Code Simplifier** | `code-simplifier@claude-plugins-official` | Reviews modified code for reuse, quality, and efficiency. Simplifies without changing functionality. |
| 10 | **Ralph Loop** | `ralph-loop@claude-plugins-official` | Iterative build-test-fix cycle. Start it, and it keeps running tests and fixing failures until green. The "Ship Loop." |
| 11 | **Claude MD Management** | `claude-md-management@claude-plugins-official` | Auto-manages CLAUDE.md files. `/revise-claude-md` updates project context based on learnings from the current session. |
| 12 | **Skill Creator** | `skill-creator@claude-plugins-official` | Build custom Claude skills from scratch or from git history patterns. |
| 13 | **Agent SDK Dev** | `agent-sdk-dev@claude-plugins-official` | Multi-agent orchestration development. Verify TypeScript and Python Agent SDK apps. |

### Testing Plugins

| # | Plugin | Slug | What It Does |
|---|--------|------|-------------|
| 14 | **Playwright** | `playwright@claude-plugins-official` | Browser automation for E2E testing. Click, navigate, screenshot, fill forms, evaluate JS — all from natural language. |
| 15 | **Security Guidance** | `security-guidance@claude-plugins-official` | Vulnerability detection and secure coding practices. OWASP Top 10 scanning. |
| 16 | **Pyright LSP** | `pyright-lsp@claude-plugins-official` | Python type checking and diagnostics via Pyright language server. |
| 17 | **QoD Skills** | `qodo-skills@claude-plugins-official` | Quality-focused testing strategies. Organization and repo-level coding rules. |

### Integration Plugins

| # | Plugin | Slug | What It Does |
|---|--------|------|-------------|
| 18 | **GitHub** | `github@claude-plugins-official` | GitHub PR/issue/branch management directly from Claude. |
| 19 | **Figma** | `figma@claude-plugins-official` | Design-to-code. Read Figma designs, get screenshots, extract code, manage Code Connect mappings. |
| 20 | **Slack** | `slack@claude-plugins-official` | Send messages, read channels, search, create canvases, schedule messages. `/channel-digest`, `/standup`, `/summarize-channel`. |
| 21 | **Atlassian** | `atlassian@claude-plugins-official` | Jira/Confluence integration. Triage issues, generate status reports, spec-to-backlog conversion, meeting notes → tasks. |
| 22 | **Pinecone** | `pinecone@claude-plugins-official` | Vector database operations. Create indexes, search records, upsert, rerank. |

### Deployment Plugins

| # | Plugin | Slug | What It Does |
|---|--------|------|-------------|
| 23 | **Vercel** | `vercel@claude-plugins-official` | Deploy to Vercel, view logs, configure projects — all from the terminal. |
| 24 | **Supabase** | `supabase@claude-plugins-official` | Database, auth, edge functions, pgvector. Execute SQL, manage migrations, deploy functions. |
| 25 | **Claude Code Setup** | `claude-code-setup@claude-plugins-official` | Analyze a codebase and recommend Claude Code configuration (hooks, MCP, settings). |

### Research & Content Plugins

| # | Plugin | Slug | What It Does |
|---|--------|------|-------------|
| 26 | **Firecrawl** | `firecrawl@claude-plugins-official` | Structured web scraping and crawling. Generate skills from documentation URLs. |
| 27 | **CodeRabbit** | `coderabbit@claude-plugins-official` | AI code review integration with thorough analysis of code changes. |
| 28 | **Frontend Design** | `frontend-design@claude-plugins-official` | Production-grade UI generation. Creates distinctive, non-generic interfaces. |
| 29 | **Learning Output Style** | `learning-output-style@claude-plugins-official` | Adaptive response formatting. Combines interactive learning with educational explanations. |
| 30 | **Serena** | `serena@claude-plugins-official` | Advanced agentic multi-step reasoning with symbolic code editing tools. Semantic code navigation without reading entire files. |

> **Slot 31:** Reserved for your own custom plugin. Build project-specific workflows with the Skill Creator plugin.

---

## Chapter 5: MCP Server Constellation

### What Are MCP Servers?

Model Context Protocol (MCP) servers extend Claude's reach beyond the terminal. Each server exposes tools that Claude can call — a memory database, a web browser, a search engine, a knowledge base.

### Plug-and-Play Servers (npm)

These servers install with zero configuration beyond an API key.

#### 1. Playwright (HIGH Priority)
```json
{
  "playwright": {
    "command": "npm",
    "args": ["exec", "@playwright/mcp@0.0.68"]
  }
}
```
**What it does:** Full browser automation. Navigate pages, click elements, fill forms, take screenshots, evaluate JavaScript. Essential for E2E testing and web interaction.
**API key required:** No

#### 2. Firecrawl (MEDIUM Priority)
```json
{
  "firecrawl": {
    "command": "npm",
    "args": ["exec", "firecrawl-mcp@3.9.0"]
  }
}
```
**What it does:** Structured web scraping. Extracts clean content from any URL. Powers the research pipeline.
**API key required:** Yes — `FIRECRAWL_API_KEY` (free tier available at firecrawl.dev)

#### 3. Perplexity (MEDIUM Priority)
```json
{
  "perplexity": {
    "command": "npm",
    "args": ["exec", "@perplexity-ai/mcp-server@0.8.2"]
  }
}
```
**What it does:** AI-powered search. Ask questions, get cited answers. Core component of the Research Stack workflow.
**API key required:** Yes — `PERPLEXITY_API_KEY`

#### 4. Memory (OPTIONAL)
```json
{
  "memory": {
    "command": "npm",
    "args": [
      "exec",
      "@modelcontextprotocol/server-memory@2026.1.26",
      "--file",
      "$HOME/.claude/memory/graph.json"
    ]
  }
}
```
**What it does:** Graph-based entity memory. Stores relationships between concepts in a local JSON file. Good for session-level knowledge.
**API key required:** No

#### 5. Hacker News (OPTIONAL)
```json
{
  "hacker-news": {
    "command": "npm",
    "args": ["exec", "hn-mcp@1.0.0"]
  }
}
```
**What it does:** Search and browse Hacker News. Useful for tech research workflows.
**API key required:** No

### SSE Servers (Self-Hosted)

These servers run as local services and connect via Server-Sent Events.

#### 6. Obsidian (HIGH Priority)
```json
{
  "obsidian": {
    "type": "sse",
    "url": "http://localhost:22360/sse"
  }
}
```
**What it does:** Bridge to your Obsidian vault. Claude can read, write, and search your notes. Requires the Obsidian Local REST API plugin (community plugin, port 22360).
**Setup:** Install "Local REST API" in Obsidian → Settings → Enable on port 22360.

#### 7. Crawl4AI (OPTIONAL)
```json
{
  "crawl4ai": {
    "type": "sse",
    "url": "http://localhost:11235/mcp/sse"
  }
}
```
**What it does:** Python-based AI web crawler. Alternative to Firecrawl for teams preferring Python pipelines.
**Setup:** `pip install crawl4ai && crawl4ai-server --port 11235`

### Cloud Servers (Claude Desktop)

These connect via Claude Desktop's native integrations — no local setup needed.

| Server | Endpoint | What It Does |
|--------|----------|-------------|
| **Gmail** | gmail.mcp.claude.com | Read/send email, create drafts, search messages |
| **Google Calendar** | gcal.mcp.claude.com | Create/update events, find free time, manage calendars |
| **Slack** | mcp.slack.com | Read/send messages, search channels, create canvases |

### Advanced: Custom MCP Servers

For power users who want persistent semantic memory or custom infrastructure control, build custom MCP servers:

**Semantic Memory Server** — Uses embedding models (e.g., Voyage AI) to store and retrieve memories by meaning, not just keywords. Survives across sessions and concurrent instances.

**Infrastructure Control Server** — Manages VPS deployments, service orchestration, and remote commands from Claude's terminal.

> **Building custom MCP servers:** Use the `@modelcontextprotocol/sdk` npm package. Each server exposes tools via the MCP protocol. Claude discovers and calls these tools automatically.

---

## Chapter 6: Lifecycle Hooks

### What Are Hooks?

Hooks are shell commands that execute automatically in response to Claude Code lifecycle events. They run before or after specific actions, enabling guardrails, automation, and context injection.

### Hook 1: Notification (Attention Required)
**Event:** `Notification`
**When:** Claude needs human input and the terminal is in the background.
```bash
osascript -e 'display notification "Claude needs input" with title "Claude Code" sound name "Ping"'
```
**Why:** You're working in another app. Claude finishes a task and needs approval. This pings you with a macOS notification so you don't leave it waiting.

### Hook 2: Session Backup (PreCompact)
**Event:** `PreCompact`
**When:** Before Claude compresses the conversation to free context.
```bash
mkdir -p ~/.claude/backups && \
cp ~/.claude/current-session.jsonl \
   ~/.claude/backups/session-$(date +%Y%m%d-%H%M%S).jsonl
```
**Why:** Context compaction is lossy. This saves the full session transcript before compression, so you never lose work. Advanced: pipe a summary to your semantic memory server.

### Hook 3: File Guard (PreToolUse — Edit|Write)
**Event:** `PreToolUse` | **Matcher:** `Edit|Write`
**When:** Before Claude edits or creates any file.
```python
import json, sys
data = json.load(sys.stdin)
path = data.get('tool_input', {}).get('file_path', '')
GUARDED = ['.env', 'package-lock.json', '.git/', 'supabase/migrations/']
sys.exit(2 if any(p in path for p in GUARDED) else 0)
```
**Why:** Prevents Claude from modifying sensitive files (secrets, lockfiles, git internals, database migrations) without explicit approval. Exit code 2 = block the action.

### Hook 4: Commit Gate (PreToolUse — Bash)
**Event:** `PreToolUse` | **Matcher:** `Bash`
**When:** Before Claude runs any bash command containing `git commit`.
```python
#!/usr/bin/env python3
"""
Blocks git commits in TypeScript projects if tsc --noEmit fails.
Exit 0 = allow, Exit 2 = block.
"""
import json, sys, subprocess, os

data = json.load(sys.stdin)
cmd = data.get('tool_input', {}).get('command', '')

if 'git commit' not in cmd:
    sys.exit(0)

if not (os.path.exists('tsconfig.json') or os.path.exists('package.json')):
    sys.exit(0)

if os.path.exists('tsconfig.json'):
    result = subprocess.run(
        ['npx', 'tsc', '--noEmit'],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        print(f"COMMIT BLOCKED: TypeScript errors found:\n{result.stderr[:1000]}")
        sys.exit(2)

sys.exit(0)
```
**Why:** Zero TypeScript errors reach your git history. Every commit is type-safe. This is the single highest-ROI hook in the stack.

### Hook 5: Auto-Lint (PostToolUse — Edit|Write)
**Event:** `PostToolUse` | **Matcher:** `Edit|Write`
**When:** After Claude edits or creates a TypeScript/JavaScript file.
```python
import json, sys, subprocess, os
data = json.load(sys.stdin)
path = data.get('tool_input', {}).get('file_path', '')
ext = os.path.splitext(path)[1]
results = []
if ext in ['.ts', '.tsx']:
    r = subprocess.run(['npx', 'tsc', '--noEmit'],
        capture_output=True, text=True, timeout=30)
    results.append(r.stderr[:500])
if ext in ['.js', '.jsx', '.ts', '.tsx']:
    r = subprocess.run(['npx', 'eslint', path],
        capture_output=True, text=True, timeout=30)
    results.append(r.stdout[:500])
output = '\n'.join(r for r in results if r.strip())
if output.strip():
    print(output)
```
**Why:** Immediate feedback. Claude sees type errors and lint warnings right after editing, and self-corrects without you having to ask.

### Hook 6: Session Context (SessionStart)
**Event:** `SessionStart`
**When:** Every time a new Claude Code session starts.
```bash
echo '=== Git Status ===' && \
git status --short 2>/dev/null || echo 'Not a git repo'
echo ''
echo '=== CLAUDE.md ===' && \
cat CLAUDE.md 2>/dev/null || echo 'No CLAUDE.md'
echo ''
echo '=== Open Issues ===' && \
gh issue list --limit 5 2>/dev/null || echo 'gh not available'
```
**Why:** Claude starts every session knowing: what branch you're on, what's changed, what your project context is, and what issues are open. No "where was I?" needed.

### Hook 7: CARL Context Injection (UserPromptSubmit)
**Event:** `UserPromptSubmit`
**When:** On every user message, before Claude processes it.

This hook runs the CARL engine (Chapter 7) to inject context-aware rules, routing guidance, and domain-specific instructions into every prompt. See the CARL chapter for the full deep-dive.

---

## Chapter 7: CARL — Context Augmentation & Reinforcement Layer

### What Is CARL?

CARL is a 1,073-line Python governance engine that runs as a `UserPromptSubmit` hook. On every message you send to Claude, CARL:

1. **Measures context** — Calculates remaining context window percentage
2. **Selects context bracket** — FRESH (>60%), MODERATE (40-60%), DEPLETED (<40%)
3. **Injects domain rules** — Loads relevant rules based on the current task
4. **Routes decisions** — Advises which model tier (Haiku/Sonnet/Opus) to use for spawned agents
5. **Enforces governance** — Planning requirements, file safety, cost management

### Context Brackets

| Bracket | Remaining | Behavior |
|---------|-----------|----------|
| **FRESH** | >60% | LEAN mode. Minimal injection. Full autonomy. Batch aggressively. |
| **MODERATE** | 40-60% | STANDARD mode. Reinforce key context. Summarize before implementing. |
| **DEPLETED** | <40% | PROTECTIVE mode. Use subagent isolation. Avoid large operations. Suggest compaction. |

### Domain Rules

CARL organizes rules into domains that load based on context:

- **GLOBAL** (always loaded) — File safety, path conventions, planning router, testing requirements
- **ROUTING** (loaded when spawning agents) — Model selection guidance: Haiku for cheap/fast, Sonnet for standard work, Opus for complex/critical
- **COMMANDS** (loaded on demand) — Custom command behaviors

### The Planning Router

CARL's most powerful feature: automatic planning depth detection.

| Task Type | CARL Action |
|-----------|-------------|
| Trivial (<10 LOC, single file) | Skip planning — just implement |
| Bug fix / small change | Route to `/planning-stack --shallow` |
| Standard feature (multi-file) | Route to `/planning-stack` (default depth) |
| Architecture / system design | Route to `/planning-stack --deep --tech` |
| Context depleted (<40%) | Route to `/plan` (subagent isolation) |

### Building Your Own CARL

CARL is customizable via a manifest system:

```yaml
# ~/.claude/carl-manifest.yaml
domains:
  global:
    name: always_on
    rules:
      - "Use absolute paths in all programming"
      - "Read files before editing them"
      - "Prefer editing existing files over creating new ones"
      - "Keep changes minimal and focused"
  routing:
    name: routing
    trigger_keywords: [model, agent, task, spawn, haiku, sonnet, opus]
    rules:
      - "HAIKU: Use for fast, low-cost tasks"
      - "SONNET: Use for standard implementation work"
      - "OPUS: Use for complex, high-stakes work"
```

---

## Chapter 8: Agent Teams

### What Are Agent Teams?

Agent Teams enable Claude Code to spawn specialized sub-agents for different task types. Instead of one generalist agent doing everything, you get a team of specialists.

**Enable with:**
```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

### The Five Roles

| Role | Model Tier | Purpose |
|------|-----------|---------|
| **Architect** | Opus | System design, architecture decisions, cross-system impact analysis |
| **Implementer** | Sonnet | Feature coding, standard implementation, refactoring |
| **Researcher** | Sonnet | Deep investigation, documentation analysis, codebase exploration |
| **Reviewer** | Sonnet | Code review, quality checks, security scanning, standards compliance |
| **Tester** | Sonnet | Test writing, test coverage analysis, E2E testing |

### Additional Specialized Agents

Beyond the core five, plugins provide additional agent types:

- **Scout** (Haiku) — Fast file searches, simple queries
- **Quickfix** (Haiku) — Small, targeted fixes with minimal scope
- **Planner** (Opus) — Complex feature and refactoring planning
- **Security Reviewer** (Opus) — Vulnerability detection and remediation
- **Database Reviewer** (Sonnet) — PostgreSQL optimization and schema review

### When to Use Agent Teams

- **Parallel work** — Launch architect + researcher simultaneously for independent tasks
- **Separation of concerns** — Reviewer examines code that implementer just wrote
- **Cost optimization** — Use Haiku agents for simple searches, Opus for critical decisions
- **Context protection** — Agent work happens in separate context windows, preserving your main session

---

# Part III — Skills & Workflows

## Chapter 9: Skills Encyclopedia

Skills are reusable prompt templates invoked via slash commands. The Gravity Stack includes 53 custom skills across 9 categories.

### Core Workflow Skills

| Skill | Command | What It Does |
|-------|---------|-------------|
| **Brainstorming** | `/brainstorming` | Mandatory pre-planning protocol. Asks questions one at a time, explores 2-3 approaches with tradeoffs, presents design in 200-300 word sections for validation. |
| **Planning Stack** | `/planning-stack` | Multi-source planning pipeline. Flags: `--shallow` (bug fixes), `--deep` (architecture), `--tech` (technical focus), `--devil` (adversarial review). |
| **Research Stack** | `/research-stack` | Hybrid multi-source research using web search, documentation fetching, codebase analysis, and synthesis. |
| **Init Project** | `/init-project` | Initialize new projects with `.planning/` directory, ROADMAP.md, phase structure. |
| **Plan Phase** | `/plan-phase` | Detail a specific project phase with tasks, dependencies, and verification criteria. |
| **Verify Phase** | `/verify-phase` | Validate phase implementation against requirements before marking complete. |
| **Next Phase** | `/next-phase` | Mark current phase complete and advance to the next one. |
| **Project Progress** | `/project-progress` | Show project progress dashboard with phase status, blockers, and completion percentage. |

### Development Skills

| Skill | Command | What It Does |
|-------|---------|-------------|
| **Test-Driven Development** | `/test-driven-development` | Enforces write-tests-first methodology with verification loops. |
| **Feature Dev** | `/feature-dev:feature-dev` | Guided feature development with codebase exploration and architecture focus. |
| **Quickfix** | `/quickfix` | Fix the described bug with minimal, targeted changes. |
| **Simplify** | `/simplify` | Review changed code for reuse, quality, and efficiency, then fix issues found. |
| **Review** | `/review` | Comprehensive code review against project standards. |
| **Commit** | `/commit` | Create well-structured git commits with conventional messages. |

### Frontend & Design Skills

| Skill | Command | What It Does |
|-------|---------|-------------|
| **Frontend Design** | `/frontend-design:frontend-design` | Create distinctive, production-grade UI. Avoids generic AI aesthetics. |
| **UI/UX Pro Max** | `/ui-ux-pro-max` | 50+ style patterns, advanced interaction design, accessibility-first approach. |
| **Web Design Guidelines** | `/web-design-guidelines` | Review UI code against Web Interface Guidelines for consistency and quality. |
| **Tailwind Design System** | `/tailwind-design-system` | Build scalable design systems with Tailwind. Token management, component patterns, responsive strategies. |
| **Vercel React Best Practices** | `/vercel-react-best-practices` | React and Next.js performance optimization patterns. |
| **Vercel Composition Patterns** | `/vercel-composition-patterns` | React composition patterns that scale. Server/client boundaries, data flow. |

### Research & Writing Skills

| Skill | Command | What It Does |
|-------|---------|-------------|
| **Research Stack** | `/research-stack` | Deep multi-source research using web, docs, and codebase analysis. |
| **Writing Clearly** | `/writing-clearly-and-concisely` | Prose quality enforcement. Clarity, conciseness, active voice. |
| **Writing Skills** | `/writing-skills` | Skill authoring guide. Create and edit skills with proper structure. |
| **Voice Check** | `/voice-check` | Check if written content matches the target voice and tone. |

### Project Management Skills

| Skill | Command | What It Does |
|-------|---------|-------------|
| **Morning Brief** | `/morning-brief` | Start-of-day summary: calendar, tasks, priorities, blockers. |
| **Close Day** | `/close-day` | End-of-day wrap: completed work, pending items, tomorrow's focus. |
| **Focus Update** | `/focus-update` | Update weekly focus areas and progress. |
| **Pause Work** | `/pause-work` | Save session state for cross-session handoff. |
| **Resume Work** | `/resume-work` | Resume a project from saved state with full context. |
| **Project Registry** | `/project-registry` | Index of all active projects with links and status. |
| **Drift** | `/drift` | Check if current work has drifted from the original plan. |
| **Challenge** | `/challenge` | Challenge assumptions about the current approach. |

### Advanced Skills

| Skill | Command | What It Does |
|-------|---------|-------------|
| **CARL Manager** | `/carl-manager` | Manage CARL domains and rules. Add, edit, toggle rules. |
| **Cost Management** | `/cost-management` | API budget monitoring with warning/critical/hard-cap thresholds. |
| **Playground** | `/playground` | Create interactive HTML playgrounds for prototyping. |
| **Context Engineering** | `/context-engineering-collection` | Comprehensive collection of agent context engineering patterns. |
| **Supabase Patterns** | `/supabase-patterns` | Database, auth, edge functions, RLS, and pgvector patterns. |
| **Obsidian CLI** | `/obsidian-cli` | Interact with Obsidian vaults using the CLI bridge. |
| **Vault Context** | `/vault-context` | Pull personal context from Obsidian to inform responses. |

### Content & Business Skills

| Skill | Command | What It Does |
|-------|---------|-------------|
| **Ideas** | `/ideas` | Capture and develop new product/feature ideas. |
| **Gig Generator** | `/gig-generator` | Generate platform-ready gig listings from service descriptions. |
| **Proposal Generator** | `/proposal-generator` | Generate custom proposals from job descriptions. |
| **Remotion Video** | `/remotion-video-production` | Produce programmable videos with Remotion framework. |
| **JSON Canvas** | `/json-canvas` | Create and edit JSON Canvas files for visual thinking. |
| **Obsidian Markdown** | `/obsidian-markdown` | Create Obsidian-flavored markdown with wiki links, callouts, dataview. |

---

## Chapter 10: Workflow Playbooks

### The Ship Loop (Build → Test → Fix → Ship)

The Ship Loop (`/ralph-loop:ralph-loop`) is an autonomous build-test-fix cycle:

```
┌──────────────┐
│  Write Code  │
└──────┬───────┘
       │
       ▼
┌──────────────┐     ┌──────────────┐
│  Run Tests   │────▶│  All Pass?   │
└──────────────┘     └──────┬───────┘
                        │ No    │ Yes
                        ▼       ▼
                   ┌─────────┐ ┌──────────┐
                   │Fix Error│ │  Ship It  │
                   └────┬────┘ └──────────┘
                        │
                        └──────▶ (back to Run Tests)
```

**Start it:** `/ralph-loop:ralph-loop`
**Cancel it:** `/ralph-loop:cancel-ralph`

The loop continues until all tests pass or you cancel. Each iteration focuses on the specific failure, applies minimal fixes, and re-runs.

### The Feature Development Workflow

```
1. /brainstorming              → Understand requirements, explore approaches
2. /planning-stack             → Create phased implementation plan
3. /feature-dev:feature-dev    → Guided architecture + implementation
4. /review                     → Code review against standards
5. /simplify                   → Clean up and simplify
6. /commit                     → Conventional commit
7. /ralph-loop:ralph-loop      → Autonomous test-fix loop
```

---

## Chapter 11: Research Stack

The Research Stack (`/research-stack`) is a multi-phase pipeline:

**Phase 1: Web Research** — Perplexity AI for cited answers, Firecrawl for structured page content, web search for broad discovery.

**Phase 2: Documentation Fetch** — Context7 pulls up-to-date library docs. Firecrawl extracts specific documentation pages.

**Phase 3: Codebase Analysis** — Grep, Glob, and semantic code search across the local project.

**Phase 4: Synthesis** — Consolidate findings into structured research output with confidence ratings and source citations.

**Flags:** `--deep` (exhaustive, all sources), `--shallow` (quick answers), `--tech` (focus on implementation details).

---

## Chapter 12: Planning Stack

The Planning Stack (`/planning-stack`) creates structured implementation plans:

**Phase 1: Requirements Gathering** — Parse the user's request, identify scope, surface ambiguities.

**Phase 2: Architecture Design** — Propose approach, identify files to create/modify, map dependencies.

**Phase 3: Task Decomposition** — Break into ordered tasks with verification criteria per task.

**Phase 4: Risk Assessment** — Identify pitfalls, anti-patterns, and failure modes.

**Phase 5: Devil's Advocate (optional)** — Adversarial review of the plan. Challenge assumptions, propose alternatives.

**Output:** `.planning/` directory with ROADMAP.md, phase directories, PLAN.md files, RESEARCH.md files.

**Flags:**
- `--shallow` — Bug fixes, small changes. Minimal planning overhead.
- `--deep` — Architecture, system design. Exhaustive analysis.
- `--tech` — Focus on technical implementation details.
- `--devil` — Include adversarial review phase.

---

## Chapter 13: Ship Loop

The Ship Loop is the autonomous build-test-fix cycle powered by the Ralph Loop plugin.

**How it works:**
1. You describe what you want to ship
2. Ralph writes the code
3. Ralph runs the tests
4. If tests fail, Ralph reads the error, fixes the code, and re-runs
5. Loop continues until all tests pass
6. You review the final diff

**Best for:** Bug fixes, refactors, test-covered features. Not recommended for greenfield architecture.

---

## Chapter 14: Devil's Advocate Protocol

The Devil's Advocate protocol challenges plans before implementation:

**Trigger:** Add `--devil` flag to any planning command, or use `/challenge`.

**What it does:**
1. Takes the proposed plan as input
2. Assumes the role of an adversarial reviewer
3. Challenges every assumption, dependency, and design choice
4. Proposes alternative approaches
5. Identifies failure modes the original plan missed
6. Presents findings as a "gate" — you approve or revise before implementation begins

**When to use:** Before committing to multi-day implementations, architectural decisions, or anything with high blast radius.

---

# Part IV — Design & Frontend

## Chapter 15: Design System

### Fonts

| Font | Source | Usage | Loading |
|------|--------|-------|---------|
| **Instrument Serif** | Google Fonts | Headings (h1, h2). Italic for emphasis. | `next/font/google` |
| **Satoshi** | fontshare.com | Body text. Clean, modern, readable. | `next/font/local` (self-hosted) |
| **DM Mono** | Google Fonts | Code, badges, labels, monospace. | `next/font/google` |

> **Warning:** Satoshi is NOT available on Google Fonts. Download from fontshare.com and load via `next/font/local`. See setup instructions in Chapter 20.

### Color Palette

```css
@theme {
  /* Backgrounds */
  --color-bg: #040608;
  --color-s1: #0a0e14;
  --color-s2: #111820;
  --color-s3: #1a2230;
  --color-border: #1e2a38;

  /* Accents */
  --color-electric: #00d4ff;    /* Primary — links, active states */
  --color-volt: #b8ff00;        /* Success, additions */
  --color-heat: #ff4d2e;        /* Warning, danger, removals */
  --color-nova: #c084fc;        /* Special elements */
  --color-glow: #fbbf24;        /* Highlights, CARL */
  --color-ice: #2dd4bf;         /* Tertiary */

  /* Text */
  --color-text: #e2e8f0;
  --color-dim: #7a8ba0;
  --color-muted: #455368;
}
```

> **Note:** These use Tailwind v4's `@theme` directive in CSS, NOT a `tailwind.config.ts` file.

### Visual Effects

**Grain overlay** — Subtle SVG noise texture on the body:
```css
body::after {
  content: '';
  position: fixed;
  inset: 0;
  pointer-events: none;
  background-image: url("data:image/svg+xml,..."); /* noise SVG */
  opacity: 0.025;
  z-index: 9999;
}
```

**Gradient text** — Hero headings:
```css
.gradient-text {
  background: linear-gradient(135deg, var(--color-electric), var(--color-volt));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
```

**Card hover glow:**
```css
.card {
  border: 1px solid var(--color-border);
  transition: border-color 0.2s, transform 0.2s;
}
.card:hover {
  border-color: rgba(0, 212, 255, 0.3);
  transform: translateY(-1px);
}
```

**Sticky nav:**
```css
nav {
  position: sticky;
  top: 0;
  backdrop-filter: blur(12px);
  background: rgba(4, 6, 8, 0.8);
}
```

### Layout Rules

| Property | Value |
|----------|-------|
| Max content width | 1400px, centered |
| Desktop padding | 48px vertical, 60px horizontal |
| Mobile padding | 24px vertical, 20px horizontal |
| Grid columns | 1 (mobile) → 2 (tablet) → 3 (desktop) |
| Card padding | 24px |
| Card border-radius | 10px |
| Card border | 1px solid var(--color-border) |

---

## Chapter 16: Design Library

The Gravity Stack includes a comprehensive design library with 6 complete design systems:

| System | Vibe | Theme | Primary | Fonts |
|--------|------|-------|---------|-------|
| **Shadcn UI** | Dark-first, pill buttons, monospace headings | Dark | #FF8400 | JetBrains Mono, Geist, Inter |
| **Lunaris** | Dark-first, pill-shaped, monospace headings | Dark | #FF8400 | JetBrains Mono, Geist |
| **Nitro** | Corporate/clean, sharp corners | Light | #0F5FFE | Roboto, Roboto Mono |
| **Halo** | Purple/indigo, generous rounded corners | Light | #5749F4 | Inter |
| **Welcome** | Dark-first, pill-radius, monospace headings | Dark | #FF8400 | JetBrains Mono, Geist, Inter |
| **Demo** | 14 mood boards (5 dashboards, 9 habit trackers) | Dark | Mixed | DM Sans, Inter, JetBrains Mono, Outfit, Space Grotesk |

**Contents:** 300+ components, 200+ design tokens, cross-reference index for quick lookup across systems.

---

## Chapter 17: UI/UX Intelligence

The stack includes three specialized UI/UX skills:

### `/ui-ux-pro-max`
50+ style patterns for web and mobile. Advanced interaction design, micro-animations, accessibility-first. Goes beyond "make it look nice" into intentional design decisions.

### `/web-design-guidelines`
Reviews UI code against established Web Interface Guidelines. Checks spacing, typography hierarchy, color contrast, responsive behavior, and component consistency.

### `/frontend-design:frontend-design`
Creates distinctive, production-grade UI that avoids generic AI aesthetics. Uses real design systems, intentional color choices, and proper typography — not template-looking interfaces.

---

## Chapter 18: Frontend Patterns

### Vercel React Best Practices (`/vercel-react-best-practices`)
- Server Components by default, Client Components only when needed
- Streaming and Suspense for perceived performance
- Image optimization with `next/image`
- Font optimization with `next/font`
- Route segment caching strategies

### Vercel Composition Patterns (`/vercel-composition-patterns`)
- Server/client component boundaries
- Data fetching patterns (server-side, client-side, hybrid)
- Layout composition with parallel routes
- Error boundary strategies
- Loading state patterns

### Tailwind Design System (`/tailwind-design-system`)
- Token-based design with CSS custom properties
- Component variant patterns using `cva` (class-variance-authority)
- Responsive design with mobile-first breakpoints
- Dark mode with Tailwind v4 `@theme`
- Animation utilities with `framer-motion` integration

---

# Part V — Setup & Installation

## Chapter 19: Prerequisites

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| **macOS** | Ventura 13.0+ | Sequoia 15.0+ |
| **Architecture** | Apple Silicon (M1+) | M2 Pro / M3+ |
| **Node.js** | 20.9 | 22 LTS |
| **Python** | 3.10 | 3.12 |
| **Claude Code** | Latest | Latest |
| **Subscription** | Claude Pro | Claude Max |
| **Disk space** | 2 GB | 5 GB |

---

## Chapter 20: Automated Setup

### Quick Start

```bash
git clone https://github.com/yourusername/gravity-stack.git
cd gravity-stack/toolkit
chmod +x install.sh
./install.sh
```

### What the Installer Does

```
Phase 1: Foundation
├── Xcode Command Line Tools
├── Homebrew
├── nvm + Node.js 22 LTS
├── pyenv + Python 3.12
├── Docker Desktop
├── Git + gh CLI
│
Phase 2: Claude Code
├── Claude Code CLI (npm)
├── Directory structure (~/.claude/hooks/, memory/, backups/)
├── settings.json generation
│
Phase 3: MCP Servers
├── Playwright MCP config
├── Firecrawl MCP config (requires API key)
├── Perplexity MCP config (requires API key)
├── Memory MCP config
├── Hacker News MCP config
│
Phase 4: Hooks
├── commit-gate.py
├── file-guard hook
├── notification hook
├── session-start hook
├── auto-lint hook
│
Phase 5: Verification
├── All tools installed ✓
├── Claude Code accessible ✓
├── MCP servers configured ✓
├── Hooks active ✓
└── Summary report
```

### Idempotency

Every script checks before installing:
```bash
# Pattern used throughout:
if command -v node &>/dev/null; then
  echo "✓ Node.js already installed: $(node --version)"
else
  echo "Installing Node.js..."
  nvm install 22
fi
```

Safe to re-run any time. Will never downgrade or overwrite existing configs.

---

## Chapter 21: Manual Setup Reference

For those who prefer manual installation or need to customize specific steps.

### Step 1: Install Claude Code
```bash
npm install -g @anthropic-ai/claude-code
```

### Step 2: Create Directory Structure
```bash
mkdir -p ~/.claude/{hooks,memory,backups}
```

### Step 3: Configure Plugins

Open Claude Code and install plugins from the marketplace:
```bash
claude
# Then use /install-plugin or the settings UI
```

### Step 4: Configure MCP Servers

Edit `~/.claude/settings.json` — add the `mcpServers` block from Chapter 5.

### Step 5: Install Hooks

Copy hook scripts from `toolkit/configs/` to `~/.claude/hooks/`, then reference them in the `hooks` section of `settings.json`.

### Step 6: Enable Agent Teams

Add to `settings.json`:
```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

---

## Chapter 22: Verification

Run the verification script:
```bash
./toolkit/scripts/05-verify.sh
```

Expected output:
```
╔══════════════════════════════════════╗
║   GRAVITY STACK — VERIFICATION      ║
╚══════════════════════════════════════╝

Foundation:
  ✓ Homebrew .............. 4.4.x
  ✓ Node.js .............. v22.x.x
  ✓ Python ............... 3.12.x
  ✓ Docker ............... 27.x.x
  ✓ Git .................. 2.4x.x
  ✓ gh CLI ............... 2.6x.x

Claude Code:
  ✓ CLI installed ........ claude 2.x.x
  ✓ Settings found ....... ~/.claude/settings.json
  ✓ Plugins configured ... 31
  ✓ MCP servers .......... 7 configured
  ✓ Hooks active ......... 7

Status: ALL CHECKS PASSED ✓
```

### Common Issues

| Issue | Solution |
|-------|----------|
| `claude: command not found` | Run `npm install -g @anthropic-ai/claude-code` and restart terminal |
| MCP server timeout | Check if the npm package version is pinned correctly |
| Hook permission denied | Run `chmod +x ~/.claude/hooks/*.py` |
| Node version mismatch | Run `nvm use 22` or add to `.nvmrc` |

---

# Part VI — The Documentation Site

## Chapter 23: Site Architecture

### Tech Stack (Verified March 2026)

| Technology | Version | Notes |
|-----------|---------|-------|
| Next.js | 16.1.6 | App Router, Turbopack (default bundler) |
| React | 19 (canary) | Bundled with Next.js 16 |
| Tailwind CSS | 4.2 | CSS-based config via `@import "tailwindcss"` and `@theme` |
| shadcn/ui | Latest | `npx shadcn@latest init` |
| TypeScript | 5.1+ strict | Built into Next.js 16 |

### Scaffolding Commands

```bash
# 1. Create Next.js app with all defaults
cd site
npx create-next-app@latest . --yes

# 2. Install shadcn/ui
npx shadcn@latest init

# 3. Download Satoshi font (NOT on Google Fonts)
# Download from https://www.fontshare.com/fonts/satoshi
# Place .woff2 files in site/src/fonts/

# 4. Configure fonts in layout.tsx
```

### Font Configuration

```tsx
// site/src/app/layout.tsx
import { Instrument_Serif, DM_Mono } from 'next/font/google'
import localFont from 'next/font/local'

const instrumentSerif = Instrument_Serif({
  subsets: ['latin'],
  weight: '400',
  variable: '--font-heading',
})

const dmMono = DM_Mono({
  subsets: ['latin'],
  weight: ['400', '500'],
  variable: '--font-mono',
})

const satoshi = localFont({
  src: [
    { path: '../fonts/Satoshi-Regular.woff2', weight: '400' },
    { path: '../fonts/Satoshi-Medium.woff2', weight: '500' },
    { path: '../fonts/Satoshi-Bold.woff2', weight: '700' },
  ],
  variable: '--font-body',
})
```

### Tailwind v4 Theme Configuration

```css
/* site/src/app/globals.css */
@import "tailwindcss";

@theme {
  --font-heading: var(--font-heading);
  --font-body: var(--font-body);
  --font-mono: var(--font-mono);

  --color-bg: #040608;
  --color-s1: #0a0e14;
  --color-s2: #111820;
  --color-s3: #1a2230;
  --color-border: #1e2a38;
  --color-electric: #00d4ff;
  --color-volt: #b8ff00;
  --color-heat: #ff4d2e;
  --color-nova: #c084fc;
  --color-glow: #fbbf24;
  --color-ice: #2dd4bf;
  --color-text: #e2e8f0;
  --color-dim: #7a8ba0;
  --color-muted: #455368;
}
```

> **No `tailwind.config.ts` needed.** Tailwind v4 uses CSS `@theme` blocks for all customization.

### Site Routes (11 Pages)

| Route | Page | Description |
|-------|------|-------------|
| `/` | Landing | Hero, value prop, stats, CTA |
| `/manifesto` | Philosophy | Why AI-native development matters |
| `/stack` | Full Stack | Complete tool breakdown by category |
| `/plugins` | Plugin Catalog | Filterable grid of all 31 plugins |
| `/mcp-servers` | MCP Constellation | Server configs and setup guides |
| `/hooks` | Hook Reference | All 7 hooks with code previews |
| `/carl` | CARL Deep-Dive | Governance engine explanation |
| `/agents` | Agent Teams | Team configuration and usage |
| `/architecture` | System Diagram | Full architecture visualization |
| `/setup` | Installation | Step-by-step setup guide |
| `/roadmap` | Project Roadmap | What's planned next |

### Component Library

| Component | Purpose |
|-----------|---------|
| `Nav.tsx` | Sticky navigation with backdrop blur, responsive hamburger menu |
| `Hero.tsx` | Gradient text heading, radial glow backgrounds, animated stats |
| `CodeBlock.tsx` | Syntax-highlighted code with copy-to-clipboard button (use `shiki` for highlighting) |
| `Card.tsx` | Glass-morphism card with border glow on hover |
| `Badge.tsx` | Color-coded badges by category/priority |
| `PluginCard.tsx` | Plugin display: name, publisher, description, category badge, priority |
| `HookCard.tsx` | Hook display: event type, matcher, code preview, description |
| `Callout.tsx` | Info/warning/tip callout boxes |
| `DiagramNode.tsx` | Architecture diagram building block |
| `Timeline.tsx` | Step-by-step setup visualization |

---

## Chapter 24: Build & Deploy

### Build Verification

```bash
cd site
npm run build
```

**Must produce zero errors.** Common issues:
- Missing font files (Satoshi .woff2 not downloaded)
- TypeScript strict mode violations
- Tailwind v4 `@theme` syntax errors
- Missing shadcn/ui component imports

### Deploy to Vercel

```bash
# Option 1: Vercel CLI
npm i -g vercel
vercel

# Option 2: GitHub auto-deploy
# Push to GitHub → Connect repo in Vercel dashboard → Auto-deploys from main
```

### Vercel Configuration

```json
// site/vercel.json (if needed)
{
  "framework": "nextjs",
  "buildCommand": "npm run build",
  "outputDirectory": ".next"
}
```

---

# Appendices

## Appendix A: Verified Plugin Catalog {#appendix-a}

Complete list of all 31 plugins with exact installation slugs:

| # | Plugin | Installation Slug | Publisher | Category | Priority |
|---|--------|-------------------|-----------|----------|----------|
| 1 | Everything Claude Code | `everything-claude-code@everything-claude-code` | everything-claude-code | core | essential |
| 2 | Feature Dev | `feature-dev@claude-plugins-official` | official | development | essential |
| 3 | Context7 | `context7@claude-plugins-official` | official | research | essential |
| 4 | Frontend Design | `frontend-design@claude-plugins-official` | official | design | essential |
| 5 | Code Review | `code-review@claude-plugins-official` | official | review | essential |
| 6 | Superpowers | `superpowers@claude-plugins-official` | official | core | essential |
| 7 | GitHub | `github@claude-plugins-official` | official | integration | essential |
| 8 | Ralph Loop | `ralph-loop@claude-plugins-official` | official | development | recommended |
| 9 | Code Simplifier | `code-simplifier@claude-plugins-official` | official | review | recommended |
| 10 | TypeScript LSP | `typescript-lsp@claude-plugins-official` | official | development | essential |
| 11 | Playwright | `playwright@claude-plugins-official` | official | testing | recommended |
| 12 | Commit Commands | `commit-commands@claude-plugins-official` | official | development | essential |
| 13 | Security Guidance | `security-guidance@claude-plugins-official` | official | review | recommended |
| 14 | Serena | `serena@claude-plugins-official` | official | development | recommended |
| 15 | PR Review Toolkit | `pr-review-toolkit@claude-plugins-official` | official | review | recommended |
| 16 | Claude MD Management | `claude-md-management@claude-plugins-official` | official | development | recommended |
| 17 | Figma | `figma@claude-plugins-official` | official | design | optional |
| 18 | Pyright LSP | `pyright-lsp@claude-plugins-official` | official | development | optional |
| 19 | Supabase | `supabase@claude-plugins-official` | official | deployment | optional |
| 20 | Agent SDK Dev | `agent-sdk-dev@claude-plugins-official` | official | development | optional |
| 21 | Atlassian | `atlassian@claude-plugins-official` | official | integration | optional |
| 22 | Claude Code Setup | `claude-code-setup@claude-plugins-official` | official | core | optional |
| 23 | Vercel | `vercel@claude-plugins-official` | official | deployment | recommended |
| 24 | Learning Output Style | `learning-output-style@claude-plugins-official` | official | core | optional |
| 25 | Slack | `slack@claude-plugins-official` | official | integration | optional |
| 26 | CodeRabbit | `coderabbit@claude-plugins-official` | official | review | optional |
| 27 | Pinecone | `pinecone@claude-plugins-official` | official | integration | optional |
| 28 | Firecrawl | `firecrawl@claude-plugins-official` | official | research | recommended |
| 29 | Skill Creator | `skill-creator@claude-plugins-official` | official | core | recommended |
| 30 | QoD Skills | `qodo-skills@claude-plugins-official` | official | testing | optional |
| 31 | *(Your Custom Plugin)* | *(your-plugin@your-org)* | custom | custom | optional |

## Appendix B: MCP Server Configurations {#appendix-b}

Complete `mcpServers` block for `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npm",
      "args": ["exec", "@playwright/mcp@0.0.68"]
    },
    "firecrawl": {
      "command": "npm",
      "args": ["exec", "firecrawl-mcp@3.9.0"]
    },
    "perplexity": {
      "command": "npm",
      "args": ["exec", "@perplexity-ai/mcp-server@0.8.2"]
    },
    "memory": {
      "command": "npm",
      "args": [
        "exec",
        "@modelcontextprotocol/server-memory@2026.1.26",
        "--file",
        "$HOME/.claude/memory/graph.json"
      ]
    },
    "hacker-news": {
      "command": "npm",
      "args": ["exec", "hn-mcp@1.0.0"]
    },
    "obsidian": {
      "type": "sse",
      "url": "http://localhost:22360/sse"
    },
    "crawl4ai": {
      "type": "sse",
      "url": "http://localhost:11235/mcp/sse"
    }
  }
}
```

> **API keys:** Firecrawl and Perplexity require API keys set as environment variables. Add `FIRECRAWL_API_KEY` and `PERPLEXITY_API_KEY` to your shell profile.

## Appendix C: Hook Command Reference {#appendix-c}

Complete `hooks` block for `~/.claude/settings.json`:

```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "",
        "hooks": [{
          "type": "command",
          "command": "osascript -e 'display notification \"Claude needs input\" with title \"Claude Code\" sound name \"Ping\"'"
        }]
      }
    ],
    "PreCompact": [
      {
        "matcher": "",
        "hooks": [{
          "type": "command",
          "command": "mkdir -p ~/.claude/backups && cp ~/.claude/current-session.jsonl ~/.claude/backups/session-$(date +%Y%m%d-%H%M%S).jsonl"
        }]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [{
          "type": "command",
          "command": "python3 -c \"import json, sys; data=json.load(sys.stdin); path=data.get('tool_input',{}).get('file_path',''); sys.exit(2 if any(p in path for p in ['.env', 'package-lock.json', '.git/', 'supabase/migrations/']) else 0)\""
        }]
      },
      {
        "matcher": "Bash",
        "hooks": [{
          "type": "command",
          "command": "python3 $HOME/.claude/hooks/commit-gate.py"
        }]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [{
          "type": "command",
          "command": "python3 -c \"import json, sys, subprocess, os; data=json.load(sys.stdin); path=data.get('tool_input',{}).get('file_path',''); ext=os.path.splitext(path)[1]; results=[]; [results.append(subprocess.run(['npx','tsc','--noEmit'],capture_output=True,text=True,timeout=30).stderr[:500]) if ext in ['.ts','.tsx'] else None]; [results.append(subprocess.run(['npx','eslint',path],capture_output=True,text=True,timeout=30).stdout[:500]) if ext in ['.js','.jsx','.ts','.tsx'] else None]; output='\\\\n'.join(r for r in results if r.strip()); print(output) if output.strip() else None\""
        }]
      }
    ],
    "SessionStart": [
      {
        "hooks": [{
          "type": "command",
          "command": "echo '=== Git Status ===' && git status --short 2>/dev/null || echo 'Not a git repo'; echo ''; echo '=== CLAUDE.md ===' && cat CLAUDE.md 2>/dev/null || echo 'No CLAUDE.md'; echo ''; echo '=== Open Issues ===' && gh issue list --limit 5 2>/dev/null || echo 'gh not available'"
        }]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [{
          "type": "command",
          "command": "python3 $HOME/.claude/hooks/carl-hook.py"
        }]
      }
    ]
  }
}
```

## Appendix D: Design System Tokens {#appendix-d}

Complete `@theme` block for Tailwind v4:

```css
@import "tailwindcss";

@theme {
  /* Typography */
  --font-heading: 'Instrument Serif', serif;
  --font-body: 'Satoshi', sans-serif;
  --font-mono: 'DM Mono', monospace;

  /* Backgrounds */
  --color-bg: #040608;
  --color-s1: #0a0e14;
  --color-s2: #111820;
  --color-s3: #1a2230;
  --color-border: #1e2a38;

  /* Accents */
  --color-electric: #00d4ff;
  --color-volt: #b8ff00;
  --color-heat: #ff4d2e;
  --color-nova: #c084fc;
  --color-glow: #fbbf24;
  --color-ice: #2dd4bf;

  /* Text */
  --color-text: #e2e8f0;
  --color-dim: #7a8ba0;
  --color-muted: #455368;

  /* Spacing */
  --spacing-page-x: 60px;
  --spacing-page-y: 48px;
  --spacing-page-x-mobile: 20px;
  --spacing-page-y-mobile: 24px;

  /* Radii */
  --radius-card: 10px;
  --radius-button: 8px;
  --radius-badge: 6px;

  /* Breakpoints */
  --breakpoint-sm: 640px;
  --breakpoint-md: 768px;
  --breakpoint-lg: 1024px;
  --breakpoint-xl: 1280px;
  --breakpoint-2xl: 1400px;
}
```

## Appendix E: Skills Quick-Reference {#appendix-e}

All 53 custom skills, sorted alphabetically:

| Skill | Command | Category |
|-------|---------|----------|
| Agentation | `/agentation` | development |
| Brainstorm Stack | `/brainstorm-stack` | planning |
| Brainstorming | `/brainstorming` | planning |
| CARL Manager | `/carl-manager` | governance |
| Challenge | `/challenge` | planning |
| Close Day | `/close-day` | management |
| Context Engineering | `/context-engineering-collection` | advanced |
| Cost Management | `/cost-management` | governance |
| Defuddle | `/defuddle` | research |
| Drift | `/drift` | management |
| E2E Testing Patterns | `/e2e-testing-patterns` | testing |
| Find Skills | `/find-skills` | utility |
| Focus Update | `/focus-update` | management |
| Gig Generator | `/gig-generator` | business |
| Graduate | `/graduate` | management |
| Ideas | `/ideas` | business |
| Init Project | `/init-project` | planning |
| JavaScript Testing | `/javascript-testing-patterns` | testing |
| Jr Dev | `/jr-dev` | development |
| JSON Canvas | `/json-canvas` | utility |
| Last 30 Days | `/last30days` | research |
| Morning Brief | `/morning-brief` | management |
| Next Phase | `/next-phase` | planning |
| Obsidian Bases | `/obsidian-bases` | utility |
| Obsidian CLI | `/obsidian-cli` | utility |
| Obsidian Markdown | `/obsidian-markdown` | utility |
| Pause Work | `/pause-work` | management |
| Plan Phase | `/plan-phase` | planning |
| Planning Stack | `/planning-stack` | planning |
| Playground | `/playground` | development |
| Project Connect | `/project-connect` | management |
| Project Progress | `/project-progress` | management |
| Project Registry | `/project-registry` | management |
| Proposal Generator | `/proposal-generator` | business |
| Remotion Video | `/remotion-video-production` | content |
| Research Stack | `/research-stack` | research |
| Resume Work | `/resume-work` | management |
| Skill Creator | `/skill-creator` | development |
| Supabase Patterns | `/supabase-patterns` | development |
| Tailwind Design System | `/tailwind-design-system` | design |
| Test-Driven Development | `/test-driven-development` | testing |
| Trace | `/trace` | debugging |
| UI/UX Pro Max | `/ui-ux-pro-max` | design |
| Vault Context | `/vault-context` | utility |
| Vercel Composition | `/vercel-composition-patterns` | frontend |
| Vercel React Best Practices | `/vercel-react-best-practices` | frontend |
| Verify Phase | `/verify-phase` | planning |
| Voice Check | `/voice-check` | writing |
| Web Design Guidelines | `/web-design-guidelines` | design |
| Writing Clearly | `/writing-clearly-and-concisely` | writing |
| Writing Skills | `/writing-skills` | writing |

Plus skills from plugins (Everything Claude Code alone adds 60+).

## Appendix F: Spec Corrections Log {#appendix-f}

Changes made from the original bootstrap spec, with evidence:

| Original Claim | Correction | Evidence |
|----------------|-----------|----------|
| Next.js 15 | **Next.js 16.1.6** | nextjs.org/docs (fetched 2026-03-09): "version: 16.1.6" |
| `tailwind.config.ts` | **CSS-based `@theme` in globals.css** | tailwindcss.com/docs v4.2: "No traditional tailwind.config.ts required" |
| 32 plugins | **31 plugins** | Actual `~/.claude/settings.json` `enabledPlugins` has 31 entries |
| Satoshi via Google Fonts | **Self-hosted via `next/font/local`** | Satoshi is by Indian Type Foundry, distributed via fontshare.com |
| `--typescript --tailwind --app --src-dir --use-npm` | **`--yes` flag** for defaults | Next.js 16 changed interactive prompts; `--yes` enables all recommended defaults |
| `create-next-app` installs Next.js 15 | Installs **Next.js 16** | `npx create-next-app@latest` as of March 2026 |
| `tailwind.config.ts` for custom theme | **`@theme` directive in CSS** | Tailwind v4 migration guide; CSS-first configuration |

---

*The Gravity Stack — Built by humans and AI, working together.*
*MIT License · 2026*
