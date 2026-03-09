import { Card } from "@/components/Card";
import { Badge } from "@/components/Badge";

export const metadata = {
  title: "Roadmap",
  description: "What's planned next for the Gravity Stack.",
};

const roadmapItems = [
  {
    status: "planned" as const,
    title: "Interactive Plugin Explorer",
    description: "Filterable, searchable grid with live category tabs and priority indicators. Install commands copyable with one click.",
  },
  {
    status: "planned" as const,
    title: "CARL Configuration Builder",
    description: "Visual tool for building CARL manifests. Define domains, add rules, set trigger keywords — generates the YAML for you.",
  },
  {
    status: "planned" as const,
    title: "Hook Playground",
    description: "Test hooks in a sandboxed environment. See what would be blocked, what context gets injected, what notifications fire.",
  },
  {
    status: "planned" as const,
    title: "MCP Server Health Dashboard",
    description: "Real-time status of all configured MCP servers. See which are running, which have errors, and connection latency.",
  },
  {
    status: "planned" as const,
    title: "Workflow Visualizer",
    description: "Interactive flowcharts showing how skills, hooks, CARL, and agents connect during common workflows like Ship Loop and Feature Dev.",
  },
  {
    status: "planned" as const,
    title: "Community Configs",
    description: "Share and discover community-contributed CARL domains, hook configs, and skill collections.",
  },
  {
    status: "planned" as const,
    title: "Multi-Platform Support",
    description: "Extend the toolkit beyond macOS to support Linux and WSL environments.",
  },
  {
    status: "planned" as const,
    title: "Audit Score Tracker",
    description: "Automated scoring of your Claude Code setup against best practices. Track improvements over time.",
  },
];

const statusColors = {
  shipped: "essential" as const,
  "in-progress": "recommended" as const,
  planned: "optional" as const,
};

export default function RoadmapPage() {
  return (
    <div className="max-w-[1400px] mx-auto px-5 md:px-[60px] py-16 md:py-24">
      <h1 className="font-heading text-4xl md:text-6xl mb-6">
        <span className="gradient-text">Roadmap</span>
      </h1>
      <p className="text-xl text-dim max-w-2xl mb-12">
        What&apos;s next for the Gravity Stack. Community input shapes priorities —
        open an issue or PR to suggest features.
      </p>

      <div className="space-y-4">
        {roadmapItems.map((item) => (
          <Card key={item.title} className="flex flex-col md:flex-row md:items-start gap-4">
            <div className="flex-shrink-0">
              <Badge variant={statusColors[item.status]}>{item.status}</Badge>
            </div>
            <div>
              <h3 className="font-medium text-text mb-1">{item.title}</h3>
              <p className="text-sm text-dim">{item.description}</p>
            </div>
          </Card>
        ))}
      </div>

      <div className="mt-16 text-center">
        <p className="text-dim mb-4">
          Have an idea? Want to contribute?
        </p>
        <a
          href="https://github.com/alexhale/gravity-stack/issues"
          className="inline-flex items-center px-6 py-3 rounded-[8px] border border-gs-border text-text hover:border-electric/30 transition-colors"
          target="_blank"
          rel="noopener noreferrer"
        >
          Open an Issue on GitHub
        </a>
      </div>
    </div>
  );
}
