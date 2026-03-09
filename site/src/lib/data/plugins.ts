export interface Plugin {
  id: number;
  name: string;
  slug: string;
  publisher: "official" | "everything-claude-code" | "custom";
  category: "core" | "development" | "testing" | "integration" | "deployment" | "research" | "design" | "review" | "custom";
  priority: "essential" | "recommended" | "optional";
  description: string;
}

export const plugins: Plugin[] = [
  { id: 1, name: "Everything Claude Code", slug: "everything-claude-code@everything-claude-code", publisher: "everything-claude-code", category: "core", priority: "essential", description: "The meta-plugin. Adds 60+ skills covering TDD, code review, security scanning, Go/Python/Java patterns, strategic compaction, content writing, deployment patterns, and more." },
  { id: 2, name: "Feature Dev", slug: "feature-dev@claude-plugins-official", publisher: "official", category: "development", priority: "essential", description: "Guided feature development: codebase exploration, architecture design, code review with confidence-based filtering. Three specialized agents." },
  { id: 3, name: "Context7", slug: "context7@claude-plugins-official", publisher: "official", category: "research", priority: "essential", description: "Fetches up-to-date documentation for any library directly into context. Eliminates hallucinated API calls by grounding Claude in real docs." },
  { id: 4, name: "Frontend Design", slug: "frontend-design@claude-plugins-official", publisher: "official", category: "design", priority: "essential", description: "Creates distinctive, production-grade UI that avoids generic AI aesthetics. Uses real design systems, intentional color choices, and proper typography." },
  { id: 5, name: "Code Review", slug: "code-review@claude-plugins-official", publisher: "official", category: "review", priority: "essential", description: "Structured code review with specialized agents for quality, security, and standards compliance." },
  { id: 6, name: "Superpowers", slug: "superpowers@claude-plugins-official", publisher: "official", category: "core", priority: "essential", description: "Advanced workflows: brainstorming protocol, plan writing, plan execution, git worktrees, parallel agent dispatch, verification loops, systematic debugging." },
  { id: 7, name: "GitHub", slug: "github@claude-plugins-official", publisher: "official", category: "integration", priority: "essential", description: "GitHub PR/issue/branch management directly from Claude." },
  { id: 8, name: "Ralph Loop", slug: "ralph-loop@claude-plugins-official", publisher: "official", category: "development", priority: "recommended", description: "Iterative build-test-fix cycle. Start it, and it keeps running tests and fixing failures until green. The Ship Loop." },
  { id: 9, name: "Code Simplifier", slug: "code-simplifier@claude-plugins-official", publisher: "official", category: "review", priority: "recommended", description: "Reviews modified code for reuse, quality, and efficiency. Simplifies without changing functionality." },
  { id: 10, name: "TypeScript LSP", slug: "typescript-lsp@claude-plugins-official", publisher: "official", category: "development", priority: "essential", description: "Language Server Protocol integration for TypeScript. Real-time type checking, go-to-definition, find references — Claude sees what your IDE sees." },
  { id: 11, name: "Playwright", slug: "playwright@claude-plugins-official", publisher: "official", category: "testing", priority: "recommended", description: "Browser automation for E2E testing. Click, navigate, screenshot, fill forms, evaluate JS — all from natural language." },
  { id: 12, name: "Commit Commands", slug: "commit-commands@claude-plugins-official", publisher: "official", category: "development", priority: "essential", description: "Conventional commit workflow. /commit generates well-structured commit messages, /commit-push-pr goes from commit to PR in one command." },
  { id: 13, name: "Security Guidance", slug: "security-guidance@claude-plugins-official", publisher: "official", category: "review", priority: "recommended", description: "Vulnerability detection and secure coding practices. OWASP Top 10 scanning." },
  { id: 14, name: "Serena", slug: "serena@claude-plugins-official", publisher: "official", category: "development", priority: "recommended", description: "Advanced agentic multi-step reasoning with symbolic code editing tools. Semantic code navigation without reading entire files." },
  { id: 15, name: "PR Review Toolkit", slug: "pr-review-toolkit@claude-plugins-official", publisher: "official", category: "review", priority: "recommended", description: "Multi-agent PR review: code reviewer, code simplifier, comment analyzer, silent failure hunter, test coverage analyzer, type design analyzer." },
  { id: 16, name: "Claude MD Management", slug: "claude-md-management@claude-plugins-official", publisher: "official", category: "development", priority: "recommended", description: "Auto-manages CLAUDE.md files. /revise-claude-md updates project context based on learnings from the current session." },
  { id: 17, name: "Figma", slug: "figma@claude-plugins-official", publisher: "official", category: "design", priority: "optional", description: "Design-to-code. Read Figma designs, get screenshots, extract code, manage Code Connect mappings." },
  { id: 18, name: "Pyright LSP", slug: "pyright-lsp@claude-plugins-official", publisher: "official", category: "development", priority: "optional", description: "Python type checking and diagnostics via Pyright language server." },
  { id: 19, name: "Supabase", slug: "supabase@claude-plugins-official", publisher: "official", category: "deployment", priority: "optional", description: "Database, auth, edge functions, pgvector. Execute SQL, manage migrations, deploy functions." },
  { id: 20, name: "Agent SDK Dev", slug: "agent-sdk-dev@claude-plugins-official", publisher: "official", category: "development", priority: "optional", description: "Multi-agent orchestration development. Verify TypeScript and Python Agent SDK apps." },
  { id: 21, name: "Atlassian", slug: "atlassian@claude-plugins-official", publisher: "official", category: "integration", priority: "optional", description: "Jira/Confluence integration. Triage issues, generate status reports, spec-to-backlog conversion, meeting notes to tasks." },
  { id: 22, name: "Claude Code Setup", slug: "claude-code-setup@claude-plugins-official", publisher: "official", category: "core", priority: "optional", description: "Analyze a codebase and recommend Claude Code configuration (hooks, MCP, settings)." },
  { id: 23, name: "Vercel", slug: "vercel@claude-plugins-official", publisher: "official", category: "deployment", priority: "recommended", description: "Deploy to Vercel, view logs, configure projects — all from the terminal." },
  { id: 24, name: "Learning Output Style", slug: "learning-output-style@claude-plugins-official", publisher: "official", category: "core", priority: "optional", description: "Adaptive response formatting. Combines interactive learning with educational explanations." },
  { id: 25, name: "Slack", slug: "slack@claude-plugins-official", publisher: "official", category: "integration", priority: "optional", description: "Send messages, read channels, search, create canvases, schedule messages." },
  { id: 26, name: "CodeRabbit", slug: "coderabbit@claude-plugins-official", publisher: "official", category: "review", priority: "optional", description: "AI code review integration with thorough analysis of code changes." },
  { id: 27, name: "Pinecone", slug: "pinecone@claude-plugins-official", publisher: "official", category: "integration", priority: "optional", description: "Vector database operations. Create indexes, search records, upsert, rerank." },
  { id: 28, name: "Firecrawl", slug: "firecrawl@claude-plugins-official", publisher: "official", category: "research", priority: "recommended", description: "Structured web scraping and crawling. Generate skills from documentation URLs." },
  { id: 29, name: "Skill Creator", slug: "skill-creator@claude-plugins-official", publisher: "official", category: "core", priority: "recommended", description: "Build custom Claude skills from scratch or from git history patterns." },
  { id: 30, name: "QoD Skills", slug: "qodo-skills@claude-plugins-official", publisher: "official", category: "testing", priority: "optional", description: "Quality-focused testing strategies. Organization and repo-level coding rules." },
  { id: 31, name: "Your Custom Plugin", slug: "your-plugin@your-org", publisher: "custom", category: "custom", priority: "optional", description: "Reserved slot for your own custom plugin. Build project-specific workflows with the Skill Creator plugin." },
];

export function getPluginsByCategory(category: Plugin["category"]): Plugin[] {
  return plugins.filter((p) => p.category === category);
}

export function getPluginsByPriority(priority: Plugin["priority"]): Plugin[] {
  return plugins.filter((p) => p.priority === priority);
}

export const pluginCategories = [...new Set(plugins.map((p) => p.category))] as const;
