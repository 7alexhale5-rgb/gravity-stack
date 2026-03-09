export interface Skill {
  name: string;
  command: string;
  category: "planning" | "development" | "testing" | "design" | "research" | "management" | "governance" | "writing" | "business" | "utility" | "frontend" | "advanced" | "content" | "debugging";
  description: string;
}

export const skills: Skill[] = [
  { name: "Brainstorming", command: "/brainstorming", category: "planning", description: "Mandatory pre-planning protocol. Asks questions one at a time, explores 2-3 approaches with tradeoffs." },
  { name: "Planning Stack", command: "/planning-stack", category: "planning", description: "Multi-source planning pipeline. Flags: --shallow, --deep, --tech, --devil." },
  { name: "Research Stack", command: "/research-stack", category: "research", description: "Hybrid multi-source research using web search, documentation fetching, codebase analysis, and synthesis." },
  { name: "Init Project", command: "/init-project", category: "planning", description: "Initialize new projects with .planning/ directory, ROADMAP.md, phase structure." },
  { name: "Plan Phase", command: "/plan-phase", category: "planning", description: "Detail a specific project phase with tasks, dependencies, and verification criteria." },
  { name: "Verify Phase", command: "/verify-phase", category: "planning", description: "Validate phase implementation against requirements before marking complete." },
  { name: "Next Phase", command: "/next-phase", category: "planning", description: "Mark current phase complete and advance to the next one." },
  { name: "Project Progress", command: "/project-progress", category: "management", description: "Show project progress dashboard with phase status, blockers, and completion percentage." },
  { name: "Test-Driven Development", command: "/test-driven-development", category: "testing", description: "Enforces write-tests-first methodology with verification loops." },
  { name: "Feature Dev", command: "/feature-dev:feature-dev", category: "development", description: "Guided feature development with codebase exploration and architecture focus." },
  { name: "Quickfix", command: "/quickfix", category: "development", description: "Fix the described bug with minimal, targeted changes." },
  { name: "Simplify", command: "/simplify", category: "development", description: "Review changed code for reuse, quality, and efficiency, then fix issues found." },
  { name: "Review", command: "/review", category: "development", description: "Comprehensive code review against project standards." },
  { name: "Commit", command: "/commit", category: "development", description: "Create well-structured git commits with conventional messages." },
  { name: "Frontend Design", command: "/frontend-design:frontend-design", category: "design", description: "Create distinctive, production-grade UI. Avoids generic AI aesthetics." },
  { name: "UI/UX Pro Max", command: "/ui-ux-pro-max", category: "design", description: "50+ style patterns, advanced interaction design, accessibility-first approach." },
  { name: "Web Design Guidelines", command: "/web-design-guidelines", category: "design", description: "Review UI code against Web Interface Guidelines for consistency and quality." },
  { name: "Tailwind Design System", command: "/tailwind-design-system", category: "design", description: "Build scalable design systems with Tailwind. Token management, component patterns." },
  { name: "Vercel React Best Practices", command: "/vercel-react-best-practices", category: "frontend", description: "React and Next.js performance optimization patterns." },
  { name: "Vercel Composition Patterns", command: "/vercel-composition-patterns", category: "frontend", description: "React composition patterns that scale. Server/client boundaries, data flow." },
  { name: "Writing Clearly", command: "/writing-clearly-and-concisely", category: "writing", description: "Prose quality enforcement. Clarity, conciseness, active voice." },
  { name: "Writing Skills", command: "/writing-skills", category: "writing", description: "Skill authoring guide. Create and edit skills with proper structure." },
  { name: "Voice Check", command: "/voice-check", category: "writing", description: "Check if written content matches the target voice and tone." },
  { name: "Morning Brief", command: "/morning-brief", category: "management", description: "Start-of-day summary: calendar, tasks, priorities, blockers." },
  { name: "Close Day", command: "/close-day", category: "management", description: "End-of-day wrap: completed work, pending items, tomorrow's focus." },
  { name: "Focus Update", command: "/focus-update", category: "management", description: "Update weekly focus areas and progress." },
  { name: "Pause Work", command: "/pause-work", category: "management", description: "Save session state for cross-session handoff." },
  { name: "Resume Work", command: "/resume-work", category: "management", description: "Resume a project from saved state with full context." },
  { name: "Project Registry", command: "/project-registry", category: "management", description: "Index of all active projects with links and status." },
  { name: "Drift", command: "/drift", category: "management", description: "Check if current work has drifted from the original plan." },
  { name: "Challenge", command: "/challenge", category: "planning", description: "Challenge assumptions about the current approach." },
  { name: "CARL Manager", command: "/carl-manager", category: "governance", description: "Manage CARL domains and rules. Add, edit, toggle rules." },
  { name: "Cost Management", command: "/cost-management", category: "governance", description: "API budget monitoring with warning/critical/hard-cap thresholds." },
  { name: "Playground", command: "/playground", category: "development", description: "Create interactive HTML playgrounds for prototyping." },
  { name: "Context Engineering", command: "/context-engineering-collection", category: "advanced", description: "Comprehensive collection of agent context engineering patterns." },
  { name: "Supabase Patterns", command: "/supabase-patterns", category: "development", description: "Database, auth, edge functions, RLS, and pgvector patterns." },
  { name: "Obsidian CLI", command: "/obsidian-cli", category: "utility", description: "Interact with Obsidian vaults using the CLI bridge." },
  { name: "Vault Context", command: "/vault-context", category: "utility", description: "Pull personal context from Obsidian to inform responses." },
  { name: "Ideas", command: "/ideas", category: "business", description: "Capture and develop new product/feature ideas." },
  { name: "Gig Generator", command: "/gig-generator", category: "business", description: "Generate platform-ready gig listings from service descriptions." },
  { name: "Proposal Generator", command: "/proposal-generator", category: "business", description: "Generate custom proposals from job descriptions." },
  { name: "Remotion Video", command: "/remotion-video-production", category: "content", description: "Produce programmable videos with Remotion framework." },
  { name: "JSON Canvas", command: "/json-canvas", category: "utility", description: "Create and edit JSON Canvas files for visual thinking." },
  { name: "Obsidian Markdown", command: "/obsidian-markdown", category: "utility", description: "Create Obsidian-flavored markdown with wiki links, callouts, dataview." },
  { name: "Agentation", command: "/agentation", category: "development", description: "Add Agentation visual feedback toolbar to a Next.js project." },
  { name: "Brainstorm Stack", command: "/brainstorm-stack", category: "planning", description: "Adaptive pre-planning questioning to gather context and surface decisions." },
  { name: "Defuddle", command: "/defuddle", category: "research", description: "Extract clean markdown content from web pages." },
  { name: "E2E Testing Patterns", command: "/e2e-testing-patterns", category: "testing", description: "Master end-to-end testing with Playwright and Cypress." },
  { name: "Find Skills", command: "/find-skills", category: "utility", description: "Discover and install agent skills." },
  { name: "Graduate", command: "/graduate", category: "management", description: "Promote an idea to an active project." },
  { name: "Jr Dev", command: "/jr-dev", category: "development", description: "Jr Dev agentic workflow for pipeline-driven builds." },
  { name: "Obsidian Bases", command: "/obsidian-bases", category: "utility", description: "Create and edit Obsidian Bases with views, filters, and formulas." },
  { name: "Trace", command: "/trace", category: "debugging", description: "Trace why something was built a certain way." },
];

export function getSkillsByCategory(category: Skill["category"]): Skill[] {
  return skills.filter((s) => s.category === category);
}

export const skillCategories = [...new Set(skills.map((s) => s.category))] as const;
