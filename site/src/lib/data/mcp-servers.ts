export interface MCPServer {
  name: string;
  slug: string;
  type: "npm" | "sse" | "cloud" | "cli";
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
    description: "Structured web scraping. Extracts clean content from any URL. Research Stack uses its scrape and /v2/search endpoints; the old /deep-research endpoint is deprecated.",
    config: { command: "npm", args: ["exec", "firecrawl-mcp@3.9.0"] },
  },
  {
    name: "Perplexity",
    slug: "perplexity",
    type: "npm",
    priority: "medium",
    apiKeyRequired: true,
    description: "AI-powered search. Ask questions, get cited answers. One of the reliable first-round sources in Research Stack.",
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

// Optional servers the Research Stack focus tags call when they are connected.
// Each tag has a free fallback, so none of these is required.
export const researchServers: MCPServer[] = [
  {
    name: "Exa",
    slug: "exa",
    type: "cloud",
    priority: "optional",
    apiKeyRequired: true,
    description: "Neural web search and page fetch. Used by the market focus tag for company and competitor discovery.",
    config: { type: "http", url: "https://mcp.exa.ai/mcp" },
  },
  {
    name: "DataForSEO",
    slug: "dataforseo",
    type: "npm",
    priority: "optional",
    apiKeyRequired: true,
    description: "Paid SERP, keyword and backlink data. Used by the seo focus tag; free fallbacks are Search Console, PageSpeed and site-scoped search.",
    config: { command: "npm", args: ["exec", "dataforseo-mcp-server"], env: { DATAFORSEO_USERNAME: "your-login", DATAFORSEO_PASSWORD: "your-password" } },
  },
  {
    name: "Mobbin",
    slug: "mobbin",
    type: "cloud",
    priority: "optional",
    apiKeyRequired: true,
    description: "Library of real app screens and user flows. Used by the ui-ux focus tag for pattern references. OAuth; paid Mobbin plans (beta since 2026-04).",
    config: { type: "http", url: "https://api.mobbin.com/mcp" },
  },
  {
    name: "Refero",
    slug: "refero",
    type: "cloud",
    priority: "optional",
    apiKeyRequired: true,
    description: "Searchable UI and web design references. Used by the ui-ux focus tag alongside Mobbin. OAuth or bearer token; paid Refero plan.",
    config: { type: "http", url: "https://api.refero.design/mcp" },
  },
  {
    name: "Socket",
    slug: "socket",
    type: "cloud",
    priority: "optional",
    apiKeyRequired: false,
    description: "Package supply-chain risk scores for npm, PyPI and other ecosystems. Used by the security and devtools focus tags.",
    config: { type: "http", url: "https://mcp.socket.dev/" },
  },
  {
    name: "Semgrep",
    slug: "semgrep",
    type: "cli",
    priority: "optional",
    apiKeyRequired: false,
    description: "Static analysis from the Semgrep CLI. Used by the security focus tag in audit mode (--target) on your own code.",
    config: { command: "semgrep", args: ["mcp"] },
  },
  {
    name: "Context7",
    slug: "context7",
    type: "cloud",
    priority: "optional",
    apiKeyRequired: false,
    description: "Current, version-specific library documentation. Used by the devtools focus tag. An API key raises rate limits.",
    config: { type: "http", url: "https://mcp.context7.com/mcp" },
  },
  {
    name: "DeepWiki",
    slug: "deepwiki",
    type: "cloud",
    priority: "optional",
    apiKeyRequired: false,
    description: "Generated docs and Q&A for public GitHub repositories. Used by the devtools focus tag.",
    config: { type: "http", url: "https://mcp.deepwiki.com/mcp" },
  },
  {
    name: "Figma",
    slug: "figma",
    type: "cloud",
    priority: "optional",
    apiKeyRequired: false,
    description: "Read Figma frames, components and variables. Used by the ui-ux focus tag. Signs in with your Figma account.",
    config: { type: "http", url: "https://mcp.figma.com/mcp" },
  },
  {
    name: "Chrome DevTools",
    slug: "chrome-devtools",
    type: "npm",
    priority: "optional",
    apiKeyRequired: false,
    description: "Drive Chrome and record performance traces. Used by the perf focus tag in audit mode (--target).",
    config: { command: "npm", args: ["exec", "chrome-devtools-mcp@latest"] },
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
