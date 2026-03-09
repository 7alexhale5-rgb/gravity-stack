export interface StackLayer {
  name: string;
  description: string;
  components: string[];
}

export const stackLayers: StackLayer[] = [
  {
    name: "Intelligence",
    description: "Claude Code CLI with 31 plugins providing specialized capabilities (code review, testing, deployment, design, security, etc.)",
    components: ["31 Plugins", "50 Skills", "5 Agent Roles"],
  },
  {
    name: "Governance",
    description: "CARL engine + lifecycle hooks enforce rules, inject context, gate commits, guard files, and route tasks to the right model tier.",
    components: ["CARL Engine (1,073 lines)", "7 Lifecycle Hooks", "Planning Router"],
  },
  {
    name: "Infrastructure",
    description: "MCP servers connect Claude to external systems: persistent memory, knowledge bases, browsers, web scrapers, search engines, and communication platforms.",
    components: ["7 Local MCP Servers", "3 Cloud MCP Servers", "Custom Server Support"],
  },
];

export const stackStats = {
  plugins: 31,
  mcpServers: { local: 7, cloud: 3, display: "7+3" },
  hooks: 7,
  skills: 50,
  agentRoles: 5,
  carlLines: 1073,
} as const;

export const agentRoles = [
  { name: "Architect", tier: "Opus", purpose: "System design, architecture decisions, cross-system impact analysis" },
  { name: "Implementer", tier: "Sonnet", purpose: "Feature coding, standard implementation, refactoring" },
  { name: "Researcher", tier: "Sonnet", purpose: "Deep investigation, documentation analysis, codebase exploration" },
  { name: "Reviewer", tier: "Sonnet", purpose: "Code review, quality checks, security scanning, standards compliance" },
  { name: "Tester", tier: "Sonnet", purpose: "Test writing, test coverage analysis, E2E testing" },
] as const;

export const additionalAgents = [
  { name: "Scout", tier: "Haiku", purpose: "Fast file searches, simple queries" },
  { name: "Quickfix", tier: "Haiku", purpose: "Small, targeted fixes with minimal scope" },
  { name: "Planner", tier: "Opus", purpose: "Complex feature and refactoring planning" },
  { name: "Security Reviewer", tier: "Opus", purpose: "Vulnerability detection and remediation" },
  { name: "Database Reviewer", tier: "Sonnet", purpose: "PostgreSQL optimization and schema review" },
] as const;
