export interface MCPServer {
  name: string;
  slug: string;
  type: "npm" | "sse" | "cloud";
  priority: "high" | "medium" | "optional";
  apiKeyRequired: boolean;
  description: string;
  config: Record<string, unknown>;
}

export const mcpServers: MCPServer[] = [
  {
    name: "Playwright",
    slug: "playwright",
    type: "npm",
    priority: "high",
    apiKeyRequired: false,
    description: "Full browser automation. Navigate pages, click elements, fill forms, take screenshots, evaluate JavaScript. Essential for E2E testing and web interaction.",
    config: { command: "npm", args: ["exec", "@playwright/mcp@0.0.68"] },
  },
  {
    name: "Firecrawl",
    slug: "firecrawl",
    type: "npm",
    priority: "medium",
    apiKeyRequired: true,
    description: "Structured web scraping. Extracts clean content from any URL. Powers the research pipeline.",
    config: { command: "npm", args: ["exec", "firecrawl-mcp@3.9.0"] },
  },
  {
    name: "Perplexity",
    slug: "perplexity",
    type: "npm",
    priority: "medium",
    apiKeyRequired: true,
    description: "AI-powered search. Ask questions, get cited answers. Core component of the Research Stack workflow.",
    config: { command: "npm", args: ["exec", "@perplexity-ai/mcp-server@0.8.2"] },
  },
  {
    name: "Memory",
    slug: "memory",
    type: "npm",
    priority: "optional",
    apiKeyRequired: false,
    description: "Graph-based entity memory. Stores relationships between concepts in a local JSON file. Good for session-level knowledge.",
    config: { command: "npm", args: ["exec", "@modelcontextprotocol/server-memory@2026.1.26", "--file", "$HOME/.claude/memory/graph.json"] },
  },
  {
    name: "Hacker News",
    slug: "hacker-news",
    type: "npm",
    priority: "optional",
    apiKeyRequired: false,
    description: "Search and browse Hacker News. Useful for tech research workflows.",
    config: { command: "npm", args: ["exec", "hn-mcp@1.0.0"] },
  },
  {
    name: "Obsidian",
    slug: "obsidian",
    type: "sse",
    priority: "high",
    apiKeyRequired: false,
    description: "Bridge to your Obsidian vault. Claude can read, write, and search your notes. Requires the Obsidian Local REST API plugin.",
    config: { type: "sse", url: "http://localhost:22360/sse" },
  },
  {
    name: "Crawl4AI",
    slug: "crawl4ai",
    type: "sse",
    priority: "optional",
    apiKeyRequired: false,
    description: "Python-based AI web crawler. Alternative to Firecrawl for teams preferring Python pipelines.",
    config: { type: "sse", url: "http://localhost:11235/mcp/sse" },
  },
];

export const cloudServers: { name: string; description: string }[] = [
  { name: "Gmail", description: "Read/send email, create drafts, search messages" },
  { name: "Google Calendar", description: "Create/update events, find free time, manage calendars" },
  { name: "Slack", description: "Read/send messages, search channels, create canvases" },
];

export function getServersByType(type: MCPServer["type"]): MCPServer[] {
  return mcpServers.filter((s) => s.type === type);
}

export function getServersByPriority(priority: MCPServer["priority"]): MCPServer[] {
  return mcpServers.filter((s) => s.priority === priority);
}
