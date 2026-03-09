# MCP Servers

Model Context Protocol (MCP) servers give Claude Code access to external tools and data sources. They run as separate processes and communicate with Claude through a standardized protocol, allowing Claude to call tools, read resources, and interact with services beyond the local filesystem.

## How MCP Works

An MCP server exposes **tools** (functions Claude can call) and **resources** (data Claude can read). When you configure an MCP server, Claude Code launches it as a subprocess or connects to it over the network. The server handles authentication, API calls, and data formatting, presenting a clean interface to Claude.

MCP servers are configured in `~/.claude/settings.json` under the `mcpServers` key.

## npm Servers

These servers are installed via npm and run as Node.js processes. Claude Code launches them automatically.

### Playwright

Browser automation for testing and web interaction.

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@anthropic/mcp-playwright"]
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
      "args": ["-y", "@anthropic/mcp-perplexity"],
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
      "args": ["-y", "@anthropic/mcp-memory"],
      "env": {
        "MEMORY_FILE": "~/.claude/memory/knowledge-graph.json"
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
      "args": ["-y", "mcp-hackernews"]
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

These servers connect to cloud services and are configured with OAuth or API keys.

### Gmail

Read and send emails through Gmail.

```json
{
  "mcpServers": {
    "gmail": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-gmail"],
      "env": {
        "GOOGLE_CLIENT_ID": "your-client-id",
        "GOOGLE_CLIENT_SECRET": "your-client-secret",
        "GOOGLE_REFRESH_TOKEN": "your-refresh-token"
      }
    }
  }
}
```

**Tools provided**: `search_emails`, `read_email`, `send_email`, `list_labels`

**Requirements**: Google Cloud project with Gmail API enabled. OAuth 2.0 credentials.

---

### Google Calendar

Manage calendar events and schedules.

```json
{
  "mcpServers": {
    "google-calendar": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-google-calendar"],
      "env": {
        "GOOGLE_CLIENT_ID": "your-client-id",
        "GOOGLE_CLIENT_SECRET": "your-client-secret",
        "GOOGLE_REFRESH_TOKEN": "your-refresh-token"
      }
    }
  }
}
```

**Tools provided**: `list_events`, `create_event`, `update_event`, `delete_event`

**Requirements**: Google Cloud project with Calendar API enabled. OAuth 2.0 credentials (can share credentials with Gmail).

---

### Slack

Interact with Slack workspaces.

```json
{
  "mcpServers": {
    "slack": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-slack"],
      "env": {
        "SLACK_BOT_TOKEN": "xoxb-your-token",
        "SLACK_TEAM_ID": "T0123456789"
      }
    }
  }
}
```

**Tools provided**: `send_message`, `read_channel`, `list_channels`, `search_messages`

**Requirements**: Slack app with Bot token. Create at [api.slack.com/apps](https://api.slack.com/apps).

---

## Full Configuration Example

Here is a complete `mcpServers` block with all 10 servers:

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@anthropic/mcp-playwright"]
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
      "args": ["-y", "@anthropic/mcp-perplexity"],
      "env": {
        "PERPLEXITY_API_KEY": "pplx-xxx"
      }
    },
    "memory": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-memory"],
      "env": {
        "MEMORY_FILE": "~/.claude/memory/knowledge-graph.json"
      }
    },
    "hackernews": {
      "command": "npx",
      "args": ["-y", "mcp-hackernews"]
    },
    "obsidian": {
      "type": "sse",
      "url": "http://localhost:22360/sse"
    },
    "crawl4ai": {
      "type": "sse",
      "url": "http://localhost:11235/sse"
    },
    "gmail": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-gmail"],
      "env": {
        "GOOGLE_CLIENT_ID": "xxx",
        "GOOGLE_CLIENT_SECRET": "xxx",
        "GOOGLE_REFRESH_TOKEN": "xxx"
      }
    },
    "google-calendar": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-google-calendar"],
      "env": {
        "GOOGLE_CLIENT_ID": "xxx",
        "GOOGLE_CLIENT_SECRET": "xxx",
        "GOOGLE_REFRESH_TOKEN": "xxx"
      }
    },
    "slack": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-slack"],
      "env": {
        "SLACK_BOT_TOKEN": "xoxb-xxx",
        "SLACK_TEAM_ID": "Txxx"
      }
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

Add it to `settings.json`:

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
