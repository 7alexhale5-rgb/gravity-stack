import { Card } from "@/components/Card";
import { DiagramNode } from "@/components/DiagramNode";
import { Badge } from "@/components/Badge";
import { ScrollReveal } from "@/components/ScrollReveal";
import { SectionDivider } from "@/components/SectionDivider";

export const metadata = {
  title: "Architecture",
  description: "Full system architecture diagram and layer descriptions.",
};

const architectureDiagram = `┌─────────────────────────────────────────────────────────────┐
│                     YOUR TERMINAL                          │
│  ┌───────────────────────────────────────────────────────┐ │
│  │                   CLAUDE CODE CLI                     │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐            │ │
│  │  │ 31       │  │ 7+3 MCP  │  │ 7        │            │ │
│  │  │ Plugins  │  │ Servers  │  │ Hooks    │            │ │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘            │ │
│  │       │              │              │                  │ │
│  │  ┌────▼──────────────▼──────────────▼─────┐           │ │
│  │  │           CARL Engine (1,073 lines)     │           │ │
│  │  │   Context Brackets · Domain Rules ·     │           │ │
│  │  │   Model Routing · Cost Management       │           │ │
│  │  └────────────────┬───────────────────────┘           │ │
│  │                   │                                    │ │
│  │  ┌────────────────▼───────────────────────┐           │ │
│  │  │         Agent Teams (5 Roles)           │           │ │
│  │  │  Architect · Implementer · Researcher   │           │ │
│  │  │  Reviewer · Tester                      │           │ │
│  │  └────────────────────────────────────────┘           │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ Memory Layer │  │ Obsidian     │  │ Playwright   │    │
│  │ (Semantic)   │  │ (Knowledge)  │  │ (Browser)    │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ Firecrawl    │  │ Perplexity   │  │ Hacker News  │    │
│  │ (Scraping)   │  │ (Search)     │  │ (Feed)       │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
└────────────────────────────────────────────────────────────┘`;

export default function ArchitecturePage() {
  return (
    <div className="max-w-[1400px] mx-auto px-5 md:px-[60px] py-16 md:py-24">
      <h1 className="font-heading text-4xl md:text-6xl mb-6">
        <span className="gradient-text">Architecture</span>
      </h1>
      <p className="text-xl text-dim max-w-2xl mb-12">
        The complete system architecture — three layers working in concert inside
        your terminal.
      </p>

      <ScrollReveal>
        <Card className="mb-16 overflow-x-auto">
          <pre className="font-mono text-xs md:text-sm text-electric leading-relaxed whitespace-pre">
            {architectureDiagram}
          </pre>
        </Card>
      </ScrollReveal>

      <SectionDivider className="mb-12" />

      <ScrollReveal>
        <h2 className="font-heading text-3xl text-text mb-8">The Three Layers</h2>
      </ScrollReveal>

      <div className="space-y-8 mb-16">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <ScrollReveal delay={0}>
            <Card className="lg:col-span-1">
              <Badge variant="essential">Layer 1</Badge>
              <h3 className="font-heading text-2xl text-text mt-3 mb-2">Intelligence</h3>
              <p className="text-sm text-dim mb-4">
                Claude Code CLI with 31 plugins providing specialized capabilities.
              </p>
              <div className="space-y-2">
                <DiagramNode label="31 Plugins" sublabel="Code review, testing, deployment, design, security" variant="primary" />
                <DiagramNode label="53 Skills" sublabel="Reusable prompt templates" variant="primary" />
                <DiagramNode label="5 Agent Roles" sublabel="Architect, Implementer, Researcher, Reviewer, Tester" variant="primary" />
              </div>
            </Card>
          </ScrollReveal>

          <ScrollReveal delay={0.06}>
            <Card className="lg:col-span-1">
              <Badge variant="recommended">Layer 2</Badge>
              <h3 className="font-heading text-2xl text-text mt-3 mb-2">Governance</h3>
              <p className="text-sm text-dim mb-4">
                CARL engine + lifecycle hooks enforce rules and route tasks.
              </p>
              <div className="space-y-2">
                <DiagramNode label="CARL Engine" sublabel="1,073 lines of governance" variant="accent" />
                <DiagramNode label="7 Hooks" sublabel="Commit gate, file guard, auto-lint, etc." variant="accent" />
                <DiagramNode label="Planning Router" sublabel="Auto-detects task complexity" variant="accent" />
              </div>
            </Card>
          </ScrollReveal>

          <ScrollReveal delay={0.12}>
            <Card className="lg:col-span-1">
              <Badge variant="optional">Layer 3</Badge>
              <h3 className="font-heading text-2xl text-text mt-3 mb-2">Infrastructure</h3>
              <p className="text-sm text-dim mb-4">
                MCP servers connecting Claude to external systems.
              </p>
              <div className="space-y-2">
                <DiagramNode label="7 Local Servers" sublabel="Playwright, Memory, Obsidian, etc." />
                <DiagramNode label="3 Cloud Servers" sublabel="Gmail, Calendar, Slack" />
                <DiagramNode label="Custom Servers" sublabel="Build your own via MCP SDK" />
              </div>
            </Card>
          </ScrollReveal>
        </div>
      </div>

      <SectionDivider className="mb-12" />

      <ScrollReveal>
        <h2 className="font-heading text-3xl text-text mb-6">Project Structure</h2>
      </ScrollReveal>
      <ScrollReveal delay={0.06}>
        <Card>
          <pre className="font-mono text-sm text-dim leading-relaxed">
{`gravity-stack/
├── site/                       # Next.js 16 documentation site
│   ├── src/
│   │   ├── app/                # App Router pages (11 routes)
│   │   ├── components/         # Reusable UI components
│   │   └── lib/data/           # Typed data modules
│   ├── public/
│   ├── next.config.ts
│   └── package.json
├── toolkit/                    # Automated setup scripts
│   ├── install.sh              # Master bootstrap
│   ├── scripts/                # 5 numbered phase scripts
│   ├── configs/                # Template configurations
│   └── templates/              # Project scaffolds
├── docs/                       # Deep-dive markdown docs
├── CLAUDE.md                   # Project context
├── README.md
└── LICENSE                     # MIT`}
          </pre>
        </Card>
      </ScrollReveal>
    </div>
  );
}
