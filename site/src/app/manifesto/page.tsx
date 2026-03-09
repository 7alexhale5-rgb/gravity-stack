import { Callout } from "@/components/Callout";

export const metadata = {
  title: "Manifesto — Gravity Stack",
  description: "Why AI-native development matters. The philosophy behind the Gravity Stack.",
};

const principles = [
  {
    title: "Convention over Configuration",
    description:
      "Sensible defaults that work out of the box, with escape hatches for customization. You shouldn't need to spend days configuring before you can ship.",
  },
  {
    title: "Idempotent Everything",
    description:
      "Every script, every hook, every config is safe to re-run. No fear of breaking things by running the installer twice.",
  },
  {
    title: "Memory is Architecture",
    description:
      "Persistent semantic memory transforms sessions from stateless to cumulative. Your AI doesn't forget what you decided last week.",
  },
  {
    title: "Governance Scales Creativity",
    description:
      "Automated guardrails (hooks, CARL, commit gates) free you to move fast without breaking things. More freedom through structure.",
  },
  {
    title: "Open by Default",
    description:
      "Every piece of this stack is free, documented, and forkable. No vendor lock-in, no hidden configs, no sanitized examples.",
  },
];

export default function ManifestoPage() {
  return (
    <div className="max-w-[1400px] mx-auto px-5 md:px-[60px] py-16 md:py-24">
      <h1 className="font-heading text-4xl md:text-6xl mb-6">
        <span className="gradient-text">The Manifesto</span>
      </h1>

      <div className="max-w-3xl space-y-8">
        <p className="text-xl text-dim leading-relaxed">
          The AI-native developer doesn&apos;t use AI as a copilot. They build{" "}
          <span className="text-text font-medium">systems</span> where AI is
          the primary interface to their entire development environment — code,
          infrastructure, memory, deployment, communication, and design — all
          accessible through natural language in a single terminal.
        </p>

        <p className="text-lg text-dim leading-relaxed">
          This isn&apos;t about typing less. It&apos;s about{" "}
          <span className="text-electric">thinking at a higher altitude</span>.
          When your AI agent can read your codebase semantically, recall
          decisions from six months ago, enforce your team&apos;s coding
          standards automatically, run your tests, deploy your infrastructure,
          manage your project board, and catch your mistakes before they reach
          git — you stop being a typist and start being an architect.
        </p>

        <Callout variant="tip" title="The Gravity Stack">
          The blueprint for building that environment.
        </Callout>

        <h2 className="font-heading text-3xl text-text pt-8">
          Core Principles
        </h2>

        <div className="space-y-6">
          {principles.map((principle, i) => (
            <div key={i} className="card-glow rounded-[10px] bg-s1 p-6">
              <h3 className="font-medium text-text mb-2 flex items-center gap-3">
                <span className="text-electric font-mono text-sm">
                  {String(i + 1).padStart(2, "0")}
                </span>
                {principle.title}
              </h3>
              <p className="text-sm text-dim">{principle.description}</p>
            </div>
          ))}
        </div>

        <h2 className="font-heading text-3xl text-text pt-8">
          Why This Stack Exists
        </h2>

        <p className="text-lg text-dim leading-relaxed">
          Most Claude Code setups use 2-3 plugins and zero hooks. That&apos;s
          like buying a Ferrari and driving it in first gear.
        </p>

        <p className="text-dim leading-relaxed">
          The Gravity Stack documents a production environment that ships real
          software across multiple projects simultaneously. The exact
          configuration described here maintains 97/100 platform audit scores,
          enforces TypeScript correctness at commit time, persists semantic
          memory across sessions, and coordinates specialized AI agent teams for
          different task types.
        </p>

        <h3 className="font-medium text-text text-lg pt-4">
          What makes this different from other &ldquo;awesome lists&rdquo;:
        </h3>

        <ul className="space-y-3 text-dim">
          <li className="flex gap-3">
            <span className="text-electric">&#x2713;</span>
            Every tool is <span className="text-text">verified and running</span> in production — no theoretical recommendations
          </li>
          <li className="flex gap-3">
            <span className="text-electric">&#x2713;</span>
            Every version number is <span className="text-text">pinned and tested</span> — no &ldquo;just install the latest&rdquo;
          </li>
          <li className="flex gap-3">
            <span className="text-electric">&#x2713;</span>
            Every configuration is <span className="text-text">the actual config</span> — not a sanitized example
          </li>
          <li className="flex gap-3">
            <span className="text-electric">&#x2713;</span>
            Every workflow is <span className="text-text">documented from real usage</span> — not hypothetical patterns
          </li>
        </ul>
      </div>
    </div>
  );
}
