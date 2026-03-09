import { agentRoles, additionalAgents } from "@/lib/data/stack";
import { Card } from "@/components/Card";
import { Badge } from "@/components/Badge";
import { CodeBlock } from "@/components/CodeBlock";
import { Callout } from "@/components/Callout";
import { ScrollReveal } from "@/components/ScrollReveal";
import { SectionDivider } from "@/components/SectionDivider";

export const metadata = {
  title: "Agent Teams",
  description: "5 core agent roles plus specialized agents with model-tier routing.",
};

const enableConfig = `{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}`;

export default function AgentsPage() {
  return (
    <div className="max-w-[1400px] mx-auto px-5 md:px-[60px] py-16 md:py-24">
      <h1 className="font-heading text-4xl md:text-6xl mb-6">
        <span className="gradient-text">Agent Teams</span>
      </h1>
      <p className="text-xl text-dim max-w-2xl mb-8">
        Instead of one generalist agent doing everything, you get a team of
        specialists. Each role uses the optimal model tier for its task type.
      </p>

      <ScrollReveal>
        <Callout variant="info" title="Enable Agent Teams">
          Add this to your <code className="font-mono text-xs bg-s2 px-1.5 py-0.5 rounded">settings.json</code>:
        </Callout>
        <div className="mt-4 mb-12">
          <CodeBlock code={enableConfig} language="json" filename="settings.json" />
        </div>
      </ScrollReveal>

      <SectionDivider className="mb-12" />

      <ScrollReveal>
        <h2 className="font-heading text-3xl text-text mb-6">
          The Five Core Roles
        </h2>
      </ScrollReveal>
      <div className="space-y-4 mb-16">
        {agentRoles.map((role, i) => (
          <ScrollReveal key={role.name} delay={i * 0.06}>
            <Card className="flex flex-col md:flex-row md:items-center gap-4">
              <div className="flex items-center gap-3 flex-shrink-0 w-48">
                <h3 className="font-medium text-text">{role.name}</h3>
                <Badge variant={role.tier === "Opus" ? "essential" : "recommended"}>
                  {role.tier}
                </Badge>
              </div>
              <p className="text-sm text-dim">{role.purpose}</p>
            </Card>
          </ScrollReveal>
        ))}
      </div>

      <SectionDivider className="mb-12" />

      <ScrollReveal>
        <h2 className="font-heading text-3xl text-text mb-6">
          Additional Specialized Agents
        </h2>
        <p className="text-dim mb-6">
          Beyond the core five, plugins provide additional agent types:
        </p>
      </ScrollReveal>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-16">
        {additionalAgents.map((agent, i) => (
          <ScrollReveal key={agent.name} delay={i * 0.06}>
            <Card>
              <div className="flex items-center gap-3 mb-2">
                <h3 className="font-medium text-text">{agent.name}</h3>
                <Badge variant={agent.tier === "Opus" ? "essential" : agent.tier === "Haiku" ? "optional" : "recommended"}>
                  {agent.tier}
                </Badge>
              </div>
              <p className="text-sm text-dim">{agent.purpose}</p>
            </Card>
          </ScrollReveal>
        ))}
      </div>

      <SectionDivider className="mb-12" />

      <ScrollReveal>
        <h2 className="font-heading text-3xl text-text mb-6">
          When to Use Agent Teams
        </h2>
      </ScrollReveal>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {[
          { title: "Parallel work", desc: "Launch architect + researcher simultaneously for independent tasks" },
          { title: "Separation of concerns", desc: "Reviewer examines code that implementer just wrote" },
          { title: "Cost optimization", desc: "Use Haiku agents for simple searches, Opus for critical decisions" },
          { title: "Context protection", desc: "Agent work happens in separate context windows, preserving your main session" },
        ].map((use, i) => (
          <ScrollReveal key={use.title} delay={i * 0.06}>
            <Card>
              <h3 className="font-medium text-text mb-1">{use.title}</h3>
              <p className="text-sm text-dim">{use.desc}</p>
            </Card>
          </ScrollReveal>
        ))}
      </div>
    </div>
  );
}
