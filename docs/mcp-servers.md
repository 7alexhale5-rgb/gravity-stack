# MCP Servers

Model Context Protocol (MCP) servers give Claude Code access to external tools and data sources. They run as separate processes and communicate with Claude through a standardized protocol, allowing Claude to call tools, read resources, and interact with services beyond the local filesystem.

## How MCP Works

An MCP server exposes **tools** (functions Claude can call) and **resources** (data Claude can read). When you configure an MCP server, Claude Code launches it as a subprocess or connects to it over the network. The server handles authentication, API calls, and data formatting, presenting a clean interface to Claude.

Register servers with `claude mcp add --scope user`; Claude stores user registrations in `~/.claude.json`. Project registrations belong in `.mcp.json`, not `settings.json`. The JSON snippets below are server blocks for `.mcp.json`; review project approvals before loading them. See the [official MCP guide](https://code.claude.com/docs/en/mcp).

The installer registers five servers and preserves any existing names. Registration, connection and a successful tool call are separate checks. API-key presence alone does not prove access.

## npm Servers

These servers are installed via npm and run as Node.js processes. Claude Code launches them automatically.

### Playwright

Browser automation for testing and web interaction.

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["-y", "@playwright/mcp@0.0.68"]
    }
  }
}
```

**Tools provided**: `browser_navigate`, `browser_click`, `browser_type`, `browser_screenshot`, `browser_evaluate`

**Use cases**: End-to-end testing, form filling, screenshot capture, web scraping with JavaScript rendering.

**Requirements**: None (uses bundled Chromium).

---

### Firecrawl

Web scraping and crawling service for extracting structured content from websites.

```json
{
  "mcpServers": {
    "firecrawl": {
      "command": "npx",
      "args": ["-y", "firecrawl-mcp"],
      "env": {
        "FIRECRAWL_API_KEY": "fc-your-key-here"
      }
    }
  }
}
```

**Tools provided**: `firecrawl_scrape`, `firecrawl_crawl`, `firecrawl_search`, `firecrawl_extract`

**Use cases**: Scraping documentation, extracting structured data, competitive research, content migration.

**Requirements**: Firecrawl API key from [firecrawl.dev](https://firecrawl.dev). Free tier available.

---

### Perplexity

AI-powered web search for real-time information retrieval.

```json
{
  "mcpServers": {
    "perplexity": {
      "command": "npx",
      "args": ["-y", "@perplexity-ai/mcp-server@0.8.2"],
      "env": {
        "PERPLEXITY_API_KEY": "pplx-your-key-here"
      }
    }
  }
}
```

**Tools provided**: `perplexity_search`, `perplexity_research`

**Use cases**: Fact-checking, finding current documentation, researching libraries, answering questions about recent events.

**Requirements**: Perplexity API key from [perplexity.ai](https://perplexity.ai). Pay-per-use pricing.

---

### Memory

Knowledge graph memory server for persistent entity and relationship storage.

```json
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory@2026.1.26"],
      "env": {
        "MEMORY_FILE_PATH": "/absolute/path/to/memory/graph.json"
      }
    }
  }
}
```

**Tools provided**: `create_entity`, `create_relation`, `search_nodes`, `read_graph`, `delete_entity`

**Use cases**: Tracking project relationships, remembering user preferences, building persistent context across sessions.

**Requirements**: None. Data stored locally in the specified JSON file.

> **Note**: This is a session-scoped knowledge graph. For concurrent multi-session persistence, use a database-backed memory server like memory-layer.

---

### Hacker News

Access Hacker News stories, comments, and search.

```json
{
  "mcpServers": {
    "hackernews": {
      "command": "npx",
      "args": ["-y", "hn-mcp@1.0.0"]
    }
  }
}
```

**Tools provided**: `get_top_stories`, `get_story`, `get_comments`, `search_stories`

**Use cases**: Tech news monitoring, finding discussions about specific tools, staying current on industry trends.

**Requirements**: None.

---

## SSE Servers

These servers run as separate processes and connect over HTTP using Server-Sent Events (SSE). You start them independently and Claude Code connects to the running process.

### Obsidian

Bridge between Claude Code and an Obsidian vault for reading and writing notes.

```json
{
  "mcpServers": {
    "obsidian": {
      "type": "sse",
      "url": "http://localhost:22360/sse"
    }
  }
}
```

**Tools provided**: `read_note`, `write_note`, `search_vault`, `list_files`, `get_tags`

**Use cases**: Accessing knowledge base, writing meeting notes, searching personal documentation, syncing project context with your vault.

**Setup**:
1. Install the Obsidian MCP plugin from the Obsidian community plugins
2. Enable the plugin in Obsidian settings
3. Configure the port (default: 22360)
4. The server runs while Obsidian is open

**Requirements**: Obsidian desktop app with MCP plugin installed.

---

### Crawl4AI

Python-based web crawler with advanced extraction capabilities.

```json
{
  "mcpServers": {
    "crawl4ai": {
      "type": "sse",
      "url": "http://localhost:11235/sse"
    }
  }
}
```

**Tools provided**: `crawl_url`, `extract_content`, `crawl_sitemap`

**Setup**:
```bash
pip install crawl4ai
crawl4ai serve --port 11235
```

**Use cases**: Deep website crawling, content extraction with CSS selectors, sitemap-based crawling, handling JavaScript-heavy sites.

**Requirements**: Python 3.10+, `crawl4ai` package.

---

## Cloud Servers

Gmail, Calendar and Slack are optional integrations. The previously listed npm
packages were unverified and are not installation instructions. Select a supported
connector in the host's integration settings, complete its authorization, and prove
actual access. These services are not registered by the core toolkit installer.

---

## Research Servers (optional)

Optional add-ons used by Research Stack focus tags. They are not part of the 7+3 core, and every tag has a
free fallback. Canonical list, detection rules and fallbacks: research-stack `references/tool-registry.json`
(github.com/7alexhale5-rgb/research-stack). The site's Research Servers section renders these entries from
`site/src/lib/data/mcp-servers.ts`.

| Server | Focus tag | Auth |
| --- | --- | --- |
| Exa | market | credentials (key or sign-in) |
| DataForSEO | seo | credentials (key or sign-in) |
| Mobbin | ui-ux | credentials (key or sign-in) |
| Refero | ui-ux | credentials (key or sign-in) |
| Socket | several | none |
| Semgrep | security | none |
| Context7 | devtools | none |
| DeepWiki | devtools | none |
| Figma | ui-ux | account sign-in |
| Chrome DevTools | perf | none |

## Full Configuration Example

Here is a complete project `.mcp.json` block for the seven local core registrations.
Cloud integrations use the host settings and are omitted from this JSON.
Replace the memory file placeholder with an absolute path before use.

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["-y", "@playwright/mcp@0.0.68"]
    },
    "firecrawl": {
      "command": "npx",
      "args": ["-y", "firecrawl-mcp"],
      "env": {
        "FIRECRAWL_API_KEY": "fc-xxx"
      }
    },
    "perplexity": {
      "command": "npx",
      "args": ["-y", "@perplexity-ai/mcp-server@0.8.2"],
      "env": {
        "PERPLEXITY_API_KEY": "pplx-xxx"
      }
    },
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory@2026.1.26"],
      "env": {
        "MEMORY_FILE_PATH": "/absolute/path/to/memory/graph.json"
      }
    },
    "hackernews": {
      "command": "npx",
      "args": ["-y", "hn-mcp@1.0.0"]
    },
    "obsidian": {
      "type": "sse",
      "url": "http://localhost:22360/sse"
    },
    "crawl4ai": {
      "type": "sse",
      "url": "http://localhost:11235/sse"
    }
  }
}
```

## API Key Requirements

| Server | Key Required | Where to Get It |
|--------|-------------|-----------------|
| Playwright | No | -- |
| Firecrawl | Yes | [firecrawl.dev](https://firecrawl.dev) |
| Perplexity | Yes | [perplexity.ai](https://perplexity.ai) |
| Memory | No | -- |
| Hacker News | No | -- |
| Obsidian | No | Obsidian MCP plugin |
| Crawl4AI | No | -- |
| Gmail | Yes (OAuth) | Google Cloud Console |
| Google Calendar | Yes (OAuth) | Google Cloud Console |
| Slack | Yes (Bot Token) | [api.slack.com/apps](https://api.slack.com/apps) |

## Building Custom MCP Servers

You can build your own MCP servers using the official SDK.

### Quick Start

```bash
mkdir my-mcp-server && cd my-mcp-server
npm init -y
npm install @modelcontextprotocol/sdk
```

### Minimal Server

```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const server = new McpServer({
  name: "my-server",
  version: "1.0.0",
});

// Define a tool
server.tool(
  "greet",
  "Greet a user by name",
  { name: z.string().describe("The name to greet") },
  async ({ name }) => ({
    content: [{ type: "text", text: `Hello, ${name}!` }],
  })
);

// Start the server
const transport = new StdioServerTransport();
await server.connect(transport);
```

### Register Your Server

Add it to the project `.mcp.json`, or register its absolute executable path with `claude mcp add --scope user`:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "node",
      "args": ["./path/to/my-server/index.js"]
    }
  }
}
```

### Tips for Custom Servers

- **Keep tools focused**: Each tool should do one thing well.
- **Validate inputs**: Use Zod schemas for all tool parameters.
- **Handle errors gracefully**: Return error messages, do not throw unhandled exceptions.
- **Add descriptions**: Tool and parameter descriptions help Claude use them correctly.
- **Test locally**: Run your server with `npx @modelcontextprotocol/inspector` to test tools interactively.


## Optional OpenAI documentation

The public [OpenAI Docs MCP](https://developers.openai.com/learn/docs-mcp) exposes documentation
search and page fetching. It does not call the paid OpenAI API. Enable its registration with
`GRAVITY_INSTALL_OPENAI_DOCS=1 bash toolkit/install.sh`, or add it explicitly:

```bash
claude mcp add --scope user --transport http openai-docs https://developers.openai.com/mcp
```

Preserve an existing carrier instead of registering the same server twice. Use a search and
fetch call to prove it works. This connector is optional and does not choose your model.
