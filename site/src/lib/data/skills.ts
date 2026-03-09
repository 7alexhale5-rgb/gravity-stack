export interface Skill {
  name: string;
  command: string;
  category: "planning" | "development" | "testing" | "design" | "research" | "management" | "governance" | "writing" | "business" | "utility" | "frontend" | "advanced" | "content" | "debugging";
  description: string;
  origin: "custom" | "plugin" | "marketplace";
}

export const skills: Skill[] = [
  { name: "Planning Stack", command: "/planning-stack", category: "planning", description: "Multi-source planning pipeline. Flags: --shallow, --deep, --tech, --devil.", origin: "custom" },
  { name: "Research Stack", command: "/research-stack", category: "research", description: "Hybrid multi-source research using web search, documentation fetching, codebase analysis, and synthesis.", origin: "custom" },
  { name: "Project Progress", command: "/project-progress", category: "management", description: "Show project progress dashboard with phase status, blockers, and completion percentage.", origin: "custom" },
  { name: "Test-Driven Development", command: "/test-driven-development", category: "testing", description: "Enforces write-tests-first methodology with verification loops.", origin: "plugin" },
  { name: "Feature Dev", command: "/feature-dev:feature-dev", category: "development", description: "Guided feature development with codebase exploration and architecture focus.", origin: "marketplace" },
  { name: "Quickfix", command: "/quickfix", category: "development", description: "Fix the described bug with minimal, targeted changes.", origin: "marketplace" },
  { name: "Simplify", command: "/simplify", category: "development", description: "Review changed code for reuse, quality, and efficiency, then fix issues found.", origin: "marketplace" },
  { name: "Review", command: "/review", category: "development", description: "Comprehensive code review against project standards.", origin: "marketplace" },
  { name: "Commit", command: "/commit", category: "development", description: "Create well-structured git commits with conventional messages.", origin: "marketplace" },
  { name: "Frontend Design", command: "/frontend-design:frontend-design", category: "design", description: "Create distinctive, production-grade UI. Avoids generic AI aesthetics.", origin: "marketplace" },
  { name: "UI/UX Pro Max", command: "/ui-ux-pro-max", category: "design", description: "50+ style patterns, advanced interaction design, accessibility-first approach.", origin: "plugin" },
  { name: "Web Design Guidelines", command: "/web-design-guidelines", category: "design", description: "Review UI code against Web Interface Guidelines for consistency and quality.", origin: "plugin" },
  { name: "Tailwind Design System", command: "/tailwind-design-system", category: "design", description: "Build scalable design systems with Tailwind. Token management, component patterns.", origin: "plugin" },
  { name: "Vercel React Best Practices", command: "/vercel-react-best-practices", category: "frontend", description: "React and Next.js performance optimization patterns.", origin: "plugin" },
  { name: "Vercel Composition Patterns", command: "/vercel-composition-patterns", category: "frontend", description: "React composition patterns that scale. Server/client boundaries, data flow.", origin: "plugin" },
  { name: "Writing Clearly", command: "/writing-clearly-and-concisely", category: "writing", description: "Prose quality enforcement. Clarity, conciseness, active voice.", origin: "plugin" },
  { name: "Writing Skills", command: "/writing-skills", category: "writing", description: "Skill authoring guide. Create and edit skills with proper structure.", origin: "custom" },
  { name: "Voice Check", command: "/voice-check", category: "writing", description: "Check if written content matches the target voice and tone.", origin: "custom" },
  { name: "Morning Brief", command: "/morning-brief", category: "management", description: "Start-of-day summary: calendar, tasks, priorities, blockers.", origin: "custom" },
  { name: "Close Day", command: "/close-day", category: "management", description: "End-of-day wrap: completed work, pending items, tomorrow's focus.", origin: "custom" },
  { name: "Focus Update", command: "/focus-update", category: "management", description: "Update weekly focus areas and progress.", origin: "custom" },
  { name: "Pause Work", command: "/pause-work", category: "management", description: "Save session state for cross-session handoff.", origin: "custom" },
  { name: "Resume Work", command: "/resume-work", category: "management", description: "Resume a project from saved state with full context.", origin: "custom" },
  { name: "Project Registry", command: "/project-registry", category: "management", description: "Index of all active projects with links and status.", origin: "custom" },
  { name: "Drift", command: "/drift", category: "management", description: "Check if current work has drifted from the original plan.", origin: "custom" },
  { name: "Challenge", command: "/challenge", category: "planning", description: "Challenge assumptions about the current approach.", origin: "custom" },
  { name: "CARL Manager", command: "/carl-manager", category: "governance", description: "Manage CARL domains and rules. Add, edit, toggle rules.", origin: "custom" },
  { name: "Cost Management", command: "/cost-management", category: "governance", description: "API budget monitoring with warning/critical/hard-cap thresholds.", origin: "custom" },
  { name: "Playground", command: "/playground", category: "development", description: "Create interactive HTML playgrounds for prototyping.", origin: "plugin" },
  { name: "Context Engineering", command: "/context-engineering-collection", category: "advanced", description: "Comprehensive collection of agent context engineering patterns.", origin: "plugin" },
  { name: "Supabase Patterns", command: "/supabase-patterns", category: "development", description: "Database, auth, edge functions, RLS, and pgvector patterns.", origin: "custom" },
  { name: "Obsidian CLI", command: "/obsidian-cli", category: "utility", description: "Interact with Obsidian vaults using the CLI bridge.", origin: "custom" },
  { name: "Vault Context", command: "/vault-context", category: "utility", description: "Pull personal context from Obsidian to inform responses.", origin: "custom" },
  { name: "Ideas", command: "/ideas", category: "business", description: "Capture and develop new product/feature ideas.", origin: "custom" },
  { name: "Gig Generator", command: "/gig-generator", category: "business", description: "Generate platform-ready gig listings from service descriptions.", origin: "custom" },
  { name: "Proposal Generator", command: "/proposal-generator", category: "business", description: "Generate custom proposals from job descriptions.", origin: "custom" },
  { name: "Remotion Video", command: "/remotion-video-production", category: "content", description: "Produce programmable videos with Remotion framework.", origin: "plugin" },
  { name: "JSON Canvas", command: "/json-canvas", category: "utility", description: "Create and edit JSON Canvas files for visual thinking.", origin: "custom" },
  { name: "Obsidian Markdown", command: "/obsidian-markdown", category: "utility", description: "Create Obsidian-flavored markdown with wiki links, callouts, dataview.", origin: "custom" },
  { name: "Agentation", command: "/agentation", category: "development", description: "Add Agentation visual feedback toolbar to a Next.js project.", origin: "plugin" },
  { name: "Brainstorm Stack", command: "/brainstorm-stack", category: "planning", description: "Custom pre-planning protocol. Asks targeted questions one at a time, gathers context, surfaces decisions, and explores 2-3 approaches with tradeoffs. Part of the planning pipeline: Research → Brainstorm → Challenge → Plan.", origin: "custom" },
  { name: "Defuddle", command: "/defuddle", category: "research", description: "Extract clean markdown content from web pages.", origin: "custom" },
  { name: "E2E Testing Patterns", command: "/e2e-testing-patterns", category: "testing", description: "Master end-to-end testing with Playwright and Cypress.", origin: "plugin" },
  { name: "Find Skills", command: "/find-skills", category: "utility", description: "Discover and install agent skills.", origin: "plugin" },
  { name: "Graduate", command: "/graduate", category: "management", description: "Promote an idea to an active project.", origin: "custom" },
  { name: "Jr Dev", command: "/jr-dev", category: "development", description: "Jr Dev agentic workflow for pipeline-driven builds.", origin: "custom" },
  { name: "Obsidian Bases", command: "/obsidian-bases", category: "utility", description: "Create and edit Obsidian Bases with views, filters, and formulas.", origin: "custom" },
  { name: "Trace", command: "/trace", category: "debugging", description: "Trace why something was built a certain way.", origin: "custom" },
  { name: "Last 30 Days", command: "/last30days", category: "research", description: "Research a topic from the last 30 days across Reddit, X, and the web. Synthesizes recent discourse.", origin: "custom" },
  { name: "Project Connect", command: "/project-connect", category: "utility", description: "Bridge project context to Obsidian vault for cross-referencing and knowledge linking.", origin: "custom" },
];

export function getSkillsByCategory(category: Skill["category"]): Skill[] {
  return skills.filter((s) => s.category === category);
}

export const skillCategories = [...new Set(skills.map((s) => s.category))] as const;
