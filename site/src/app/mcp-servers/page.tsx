import { mcpServers, cloudServers } from "@/lib/data/mcp-servers";
import { Card } from "@/components/Card";
import { Badge } from "@/components/Badge";
import { CodeBlock } from "@/components/CodeBlock";
import { Callout } from "@/components/Callout";

import { PageHeader } from "@/components/PageHeader";

export const metadata = {
  title: "MCP Servers",
  description: "7+3 MCP servers connecting Claude to browsers, search engines, memory, and more.",
};

export default function MCPServersPage() {
  return (
    <div className="max-w-[1400px] mx-auto px-5 md:px-[60px] py-16 md:py-24">
      <PageHeader
        eyebrow="Layer 3 — Infrastructure"
        title="MCP Server Constellation"
        description="Model Context Protocol servers extend Claude's reach beyond the terminal. Each server exposes tools that Claude can call — a memory database, a web browser, a search engine, a knowledge base."
      />

      <h2 className="font-heading text-3xl text-text mb-6">
        Local Servers ({mcpServers.length})
      </h2>

      <div className="space-y-6 mb-16">
        {mcpServers.map((server) => (
          <Card key={server.slug} className="space-y-4">
            <div className="flex items-start justify-between">
              <h3 className="font-medium text-lg text-text">{server.name}</h3>
              <div className="flex gap-2">
                <Badge variant={server.priority}>{server.priority}</Badge>
                <Badge variant={server.type}>{server.type}</Badge>
              </div>
            </div>
            <p className="text-sm text-dim">{server.description}</p>
            {server.apiKeyRequired && (
              <Callout variant="warning" title="API Key Required">
                This server requires an API key set as an environment variable.
              </Callout>
            )}
            <CodeBlock
              code={JSON.stringify({ [server.slug]: server.config }, null, 2)}
              language="json"
              filename="~/.claude/settings.json"
            />
          </Card>
        ))}
      </div>

      <h2 className="font-heading text-3xl text-text mb-6">
        Cloud Servers ({cloudServers.length})
      </h2>
      <p className="text-dim mb-6">
        These connect via Claude Desktop&apos;s native integrations — no local setup needed.
      </p>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {cloudServers.map((server) => (
          <Card key={server.name}>
            <h3 className="font-medium text-text mb-2">{server.name}</h3>
            <p className="text-sm text-dim">{server.description}</p>
          </Card>
        ))}
      </div>
    </div>
  );
}
