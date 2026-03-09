import { Card } from "@/components/Card";
import { Badge } from "@/components/Badge";
import { CodeBlock } from "@/components/CodeBlock";
import { Callout } from "@/components/Callout";

export const metadata = {
  title: "CARL — Gravity Stack",
  description: "Context Augmentation & Reinforcement Layer: the 1,073-line governance engine.",
};

const contextBrackets = [
  {
    bracket: "FRESH",
    remaining: ">60%",
    behavior: "LEAN mode. Minimal injection. Full autonomy. Batch aggressively.",
    color: "text-volt",
  },
  {
    bracket: "MODERATE",
    remaining: "40-60%",
    behavior: "STANDARD mode. Reinforce key context. Summarize before implementing.",
    color: "text-glow",
  },
  {
    bracket: "DEPLETED",
    remaining: "<40%",
    behavior: "PROTECTIVE mode. Use subagent isolation. Avoid large operations. Suggest compaction.",
    color: "text-heat",
  },
];

const planningRouter = [
  { task: "Trivial (<10 LOC, single file)", action: "Skip planning — just implement" },
  { task: "Bug fix / small change", action: "/planning-stack --shallow" },
  { task: "Standard feature (multi-file)", action: "/planning-stack (default depth)" },
  { task: "Architecture / system design", action: "/planning-stack --deep --tech" },
  { task: "Context depleted (<40%)", action: "/plan (subagent isolation)" },
];

const carlManifestExample = `# ~/.claude/carl-manifest.yaml
domains:
  global:
    name: always_on
    rules:
      - "Use absolute paths in all programming"
      - "Read files before editing them"
      - "Prefer editing existing files over creating new ones"
      - "Keep changes minimal and focused"
  routing:
    name: routing
    trigger_keywords: [model, agent, task, spawn]
    rules:
      - "HAIKU: Use for fast, low-cost tasks"
      - "SONNET: Use for standard implementation"
      - "OPUS: Use for complex, high-stakes work"`;

export default function CARLPage() {
  return (
    <div className="max-w-[1400px] mx-auto px-5 md:px-[60px] py-16 md:py-24">
      <h1 className="font-heading text-4xl md:text-6xl mb-6">
        <span className="gradient-text">CARL</span>
      </h1>
      <p className="text-xl text-dim max-w-2xl mb-4">
        Context Augmentation &amp; Reinforcement Layer — a 1,073-line Python
        governance engine that runs as a UserPromptSubmit hook.
      </p>
      <p className="text-dim max-w-2xl mb-12">
        On every message you send to Claude, CARL measures context, selects a
        bracket, injects domain rules, routes decisions, and enforces governance.
      </p>

      <h2 className="font-heading text-3xl text-text mb-6">
        What CARL Does
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-16">
        {[
          { label: "Measures context", desc: "Calculates remaining context window percentage" },
          { label: "Selects bracket", desc: "FRESH, MODERATE, or DEPLETED mode" },
          { label: "Injects domain rules", desc: "Loads relevant rules based on current task" },
          { label: "Routes decisions", desc: "Advises which model tier for spawned agents" },
          { label: "Enforces governance", desc: "Planning requirements, file safety, costs" },
        ].map((item) => (
          <Card key={item.label}>
            <h3 className="font-medium text-text mb-1">{item.label}</h3>
            <p className="text-sm text-dim">{item.desc}</p>
          </Card>
        ))}
      </div>

      <h2 className="font-heading text-3xl text-text mb-6">
        Context Brackets
      </h2>
      <div className="space-y-4 mb-16">
        {contextBrackets.map((b) => (
          <Card key={b.bracket} className="flex flex-col md:flex-row md:items-center gap-4">
            <div className="flex-shrink-0 w-32">
              <span className={`font-mono font-bold ${b.color}`}>{b.bracket}</span>
              <div className="text-xs text-gs-muted">{b.remaining}</div>
            </div>
            <p className="text-sm text-dim">{b.behavior}</p>
          </Card>
        ))}
      </div>

      <h2 className="font-heading text-3xl text-text mb-6">
        Planning Router
      </h2>
      <Callout variant="info" title="CARL's most powerful feature">
        Automatic planning depth detection. CARL analyzes your task and routes to
        the right planning depth automatically.
      </Callout>
      <div className="mt-6 overflow-x-auto mb-16">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gs-border">
              <th className="text-left py-3 px-4 text-dim font-medium">Task Type</th>
              <th className="text-left py-3 px-4 text-dim font-medium">CARL Action</th>
            </tr>
          </thead>
          <tbody>
            {planningRouter.map((row) => (
              <tr key={row.task} className="border-b border-gs-border/50">
                <td className="py-3 px-4 text-text">{row.task}</td>
                <td className="py-3 px-4">
                  <code className="font-mono text-xs text-electric">{row.action}</code>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h2 className="font-heading text-3xl text-text mb-6">
        Domain Rules
      </h2>
      <div className="space-y-4 mb-16">
        {[
          { name: "GLOBAL", desc: "Always loaded — file safety, path conventions, planning router, testing requirements", badge: "essential" as const },
          { name: "ROUTING", desc: "Loaded when spawning agents — model selection guidance for Haiku/Sonnet/Opus tiers", badge: "recommended" as const },
          { name: "COMMANDS", desc: "Loaded on demand — custom command behaviors and overrides", badge: "optional" as const },
        ].map((domain) => (
          <Card key={domain.name} className="flex items-start gap-4">
            <Badge variant={domain.badge}>{domain.name}</Badge>
            <p className="text-sm text-dim">{domain.desc}</p>
          </Card>
        ))}
      </div>

      <h2 className="font-heading text-3xl text-text mb-6">
        Build Your Own CARL
      </h2>
      <p className="text-dim mb-6">
        CARL is customizable via a manifest system. Define your own domains,
        rules, and trigger keywords:
      </p>
      <CodeBlock code={carlManifestExample} language="yaml" filename="carl-manifest.yaml" />
    </div>
  );
}
