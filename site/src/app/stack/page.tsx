import { stackLayers, stackStats, agentRoles } from "@/lib/data/stack";
import { Card } from "@/components/Card";
import { Badge } from "@/components/Badge";
import { PageHeader } from "@/components/PageHeader";
import Link from "next/link";

export const metadata = {
  title: "The Stack",
  description: "Architecture overview of the Gravity Stack: Intelligence, Governance, and Infrastructure layers.",
};

export default function StackPage() {
  return (
    <div className="max-w-[1400px] mx-auto px-5 md:px-[60px] py-16 md:py-24">
      <PageHeader
        eyebrow="Overview"
        title="The Stack"
        description="Three layers working together: Intelligence for capabilities, Governance for guardrails, Infrastructure for reach."
      />

      <div className="space-y-6 mb-16">
        {stackLayers.map((layer, i) => (
          <Card key={i} className="relative overflow-hidden">
            <div className="flex flex-col md:flex-row md:items-start gap-6">
              <div className="flex-shrink-0">
                <span className="font-heading text-5xl text-electric/20">
                  {String(i + 1).padStart(2, "0")}
                </span>
              </div>
              <div className="flex-1">
                <h2 className="font-heading text-2xl text-text mb-2">
                  Layer {i + 1}: {layer.name}
                </h2>
                <p className="text-dim mb-4">{layer.description}</p>
                <div className="flex flex-wrap gap-2">
                  {layer.components.map((component) => (
                    <Badge key={component} variant="core">
                      {component}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>

      <h2 className="font-heading text-3xl text-text mb-6">By the Numbers</h2>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-16">
        {[
          { value: stackStats.plugins, label: "Plugins", href: "/plugins" },
          { value: stackStats.mcpServers.display, label: "MCP Servers", href: "/mcp-servers" },
          { value: stackStats.hooks, label: "Hooks", href: "/hooks" },
          { value: stackStats.skills, label: "Skills", href: "/skills" },
          { value: stackStats.agentRoles, label: "Agent Roles", href: "/agents" },
          { value: stackStats.carlLines.toLocaleString(), label: "CARL Lines", href: "/carl" },
        ].map((stat) => (
          <Link key={stat.label} href={stat.href}>
            <Card className="text-center hover:bg-s2 transition-colors">
              <div className="font-heading text-2xl text-electric mb-1">
                {stat.value}
              </div>
              <div className="text-xs text-dim">{stat.label}</div>
            </Card>
          </Link>
        ))}
      </div>

      <h2 className="font-heading text-3xl text-text mb-6">Agent Roles</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {agentRoles.map((role) => (
          <Card key={role.name}>
            <div className="flex items-center gap-3 mb-2">
              <h3 className="font-medium text-text">{role.name}</h3>
              <Badge variant={role.tier === "Opus" ? "essential" : "recommended"}>
                {role.tier}
              </Badge>
            </div>
            <p className="text-sm text-dim">{role.purpose}</p>
          </Card>
        ))}
      </div>
    </div>
  );
}
