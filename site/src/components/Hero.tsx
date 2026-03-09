import { stackStats } from "@/lib/data/stack";

export function Hero() {
  return (
    <section className="relative overflow-hidden py-24 md:py-32">
      {/* Radial glow background */}
      <div className="absolute inset-0 -z-10">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full bg-electric/5 blur-[120px]" />
      </div>
      <div className="max-w-[1400px] mx-auto px-5 md:px-[60px]">
        <h1 className="font-heading text-5xl md:text-7xl lg:text-8xl mb-6">
          <span className="gradient-text">The Gravity Stack</span>
        </h1>
        <p className="text-xl md:text-2xl text-dim max-w-2xl mb-12">
          The complete blueprint for a top 1% AI-native development environment. Open source. Documented. Ready to fork.
        </p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-12">
          <StatBlock value={stackStats.plugins} label="Plugins" />
          <StatBlock value={stackStats.mcpServers.display} label="MCP Servers" />
          <StatBlock value={stackStats.hooks} label="Hooks" />
          <StatBlock value={stackStats.skills} label="Skills" />
        </div>
        <div className="flex gap-4">
          <a
            href="/setup"
            className="inline-flex items-center px-6 py-3 rounded-[8px] bg-electric text-bg font-medium hover:bg-electric/90 transition-colors"
          >
            Get Started
          </a>
          <a
            href="https://github.com/alexhale/gravity-stack"
            className="inline-flex items-center px-6 py-3 rounded-[8px] border border-gs-border text-text hover:border-electric/30 transition-colors"
            target="_blank"
            rel="noopener noreferrer"
          >
            GitHub
          </a>
        </div>
      </div>
    </section>
  );
}

function StatBlock({ value, label }: { value: number | string; label: string }) {
  return (
    <div className="card-glow rounded-[10px] bg-s1 p-6 text-center">
      <div className="font-heading text-4xl md:text-5xl text-electric mb-2">{value}</div>
      <div className="text-sm text-dim">{label}</div>
    </div>
  );
}
