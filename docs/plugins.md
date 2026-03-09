# Plugins

Plugins extend Claude Code with new skills, integrations, and workflows. They are community-built packages that inject specialized knowledge and tool access into your coding sessions.

## How Plugins Work

A plugin is a bundled set of instructions and tools that Claude Code loads at session start. Plugins can add slash commands, system-level context, and behavioral rules. They are installed from the Claude Code marketplace and listed in your `~/.claude/settings.json` under the `enabledPlugins` key.

## Installing Plugins

1. Open Claude Code
2. Run `/plugins` or press `Ctrl+Shift+P` and search "plugins"
3. Browse the marketplace
4. Select a plugin and confirm installation
5. The plugin is added to your `settings.json` and available immediately

To uninstall, remove the plugin entry from `settings.json` or use the `/plugins` interface.

## The 31 Plugins by Category

Claude Code supports up to 32 plugin slots. Gravity Stack uses 31, reserving slot 32 for your own custom plugin.

### Core

These plugins form the foundation of the environment. Install them first.

| Plugin | What It Does |
|--------|-------------|
| **Everything Claude Code** | Extended skill library: `/plan`, `/tdd`, `/code-review`, `/e2e`, security review, postgres patterns, strategic compact. The single most important plugin. |
| **Superpowers** | Unlocks advanced agent behaviors: parallel tool calls, memory persistence, multi-step reasoning chains. |
| **Claude Code Setup** | Scaffolds new projects with `CLAUDE.md`, directory structure, and sensible defaults. Saves 30 minutes on every new project. |
| **Skill Creator** | Build your own slash-command skills from natural language descriptions. Outputs structured YAML skill files. |
| **Learning Output Style** | Adapts Claude's output format (verbose, concise, tutorial-style) based on your learning preferences. |

### Development

Day-to-day coding plugins that improve code quality and developer experience.

| Plugin | What It Does |
|--------|-------------|
| **Feature Dev** | Guided feature development workflow: codebase exploration, architecture planning, incremental implementation. |
| **TypeScript LSP** | Integrates TypeScript language server for real-time type checking, go-to-definition, and error diagnostics inside Claude sessions. |
| **Commit Commands** | Smart git workflows: conventional commits, interactive staging, branch management, changelog generation. |
| **Code Simplifier** | Analyzes code for unnecessary complexity and suggests simpler alternatives. Fights over-engineering. |
| **Ralph Loop** | Red-green-refactor loop automation. Write a failing test, make it pass, refactor. Enforces TDD discipline. |
| **Claude MD Management** | Tools for managing `CLAUDE.md` files: merging, diffing, validating, and syncing across projects. |
| **Agent SDK Dev** | Development tools for building custom Claude agents with the Agent SDK. Includes templates and debugging. |
| **Serena** | Code-aware assistant that understands project structure, dependencies, and can navigate large codebases intelligently. |
| **Pyright LSP** | Python type-checking integration via Pyright. Real-time diagnostics for Python projects. |

### Testing

Plugins focused on test authoring, security auditing, and code quality.

| Plugin | What It Does |
|--------|-------------|
| **Playwright** | End-to-end testing patterns: page object models, test generators, visual regression, network interception. |
| **Security Guidance** | Security review automation: OWASP checks, dependency auditing, secret scanning, auth flow analysis. |
| **QoD Skills** | Quality-of-Development metrics: test coverage analysis, code complexity scoring, maintainability reports. |

### Review

Code review and PR management plugins.

| Plugin | What It Does |
|--------|-------------|
| **Code Review** | Structured code review with severity levels, inline suggestions, and architectural feedback. |
| **PR Review Toolkit** | GitHub PR review automation: summary generation, diff analysis, review comment drafting. |
| **CodeRabbit** | AI-powered PR review integration. Automated review comments on pull requests. |

### Integration

Connect Claude Code to external services and platforms.

| Plugin | What It Does |
|--------|-------------|
| **GitHub** | GitHub API integration: issues, PRs, actions, releases, repository management without leaving Claude. |
| **Figma** | Read Figma designs and extract components, tokens, and layout information for implementation. |
| **Slack** | Send messages, read channels, and manage Slack workflows from Claude Code sessions. |
| **Atlassian** | Jira and Confluence integration: read tickets, update status, search documentation. |
| **Pinecone** | Vector database operations: upsert, query, and manage Pinecone indexes for RAG workflows. |

### Deployment

Ship code to production.

| Plugin | What It Does |
|--------|-------------|
| **Vercel** | Deploy to Vercel, manage projects, check deployment status, read build logs. |
| **Supabase** | Supabase project management: database migrations, edge functions, auth config, storage. |

### Research

Gather information from the web and documentation.

| Plugin | What It Does |
|--------|-------------|
| **Context7** | Pull up-to-date library documentation into context. Avoids hallucinating outdated APIs. |
| **Firecrawl** | Web scraping and crawling. Extract structured data from websites. |

### Design

UI and frontend design plugins.

| Plugin | What It Does |
|--------|-------------|
| **Frontend Design** | High-quality frontend UI generation. Avoids generic AI aesthetics. Produces production-grade components. |

## Priority Tiers

### Essential (Install First)

These plugins provide the highest value and should be installed before anything else.

1. Everything Claude Code
2. Feature Dev
3. GitHub
4. Vercel
5. Context7
6. Code Review
7. Frontend Design
8. Superpowers
9. Claude Code Setup

### Recommended (High Value)

Install these after the essentials. They significantly improve daily workflow.

- TypeScript LSP
- Commit Commands
- Playwright
- Security Guidance
- PR Review Toolkit
- Supabase
- Firecrawl
- Serena
- Code Simplifier

### Optional (Use-Case Specific)

Install based on your stack and needs.

- Figma (if you use Figma for design)
- Slack (if your team uses Slack)
- Atlassian (if you use Jira/Confluence)
- Pinecone (if you use vector databases)
- Pyright LSP (if you write Python)
- CodeRabbit (if you want automated PR reviews)
- Ralph Loop (if you practice strict TDD)
- Agent SDK Dev (if you build custom agents)
- Claude MD Management (if you manage many projects)
- Skill Creator (if you want custom skills)
- Learning Output Style (if you want adaptive output)
- QoD Skills (if you track code quality metrics)

## Slot 31 Reserved

Slot 31 is intentionally left open for your own custom plugin. Use the Skill Creator plugin or build one manually by following the plugin authoring guide in the Claude Code documentation. This gives you room to add project-specific or team-specific tooling without hitting the 32-plugin limit.

## Plugin Configuration

Plugins are stored in `~/.claude/settings.json`:

```json
{
  "enabledPlugins": [
    "everything-claude-code",
    "superpowers",
    "claude-code-setup",
    "skill-creator",
    "learning-output-style",
    "feature-dev",
    "typescript-lsp",
    "commit-commands",
    "code-simplifier",
    "ralph-loop",
    "claude-md-management",
    "agent-sdk-dev",
    "serena",
    "pyright-lsp",
    "playwright",
    "security-guidance",
    "qod-skills",
    "code-review",
    "pr-review-toolkit",
    "coderabbit",
    "github",
    "figma",
    "slack",
    "atlassian",
    "pinecone",
    "vercel",
    "supabase",
    "context7",
    "firecrawl",
    "frontend-design"
  ]
}
```

## Tips

- **Plugin conflicts**: If two plugins provide overlapping slash commands, the one listed first in `enabledPlugins` takes priority.
- **Performance**: Each plugin adds to session startup time. If sessions feel slow, audit which plugins you actually use.
- **Updates**: Plugins update automatically from the marketplace. Pin versions in `settings.json` if you need stability.
- **Debugging**: Run `/plugins status` to see which plugins loaded successfully and which failed.
