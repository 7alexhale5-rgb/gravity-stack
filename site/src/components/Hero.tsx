import { stackStats } from "@/lib/data/stack";

export function Hero() {
  return (
    <section className="relative overflow-hidden py-24 md:py-36">
      {/* Layered glow background */}
      <div className="absolute inset-0 -z-10">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[600px] rounded-full bg-electric/5 blur-[150px]" />
        <div className="absolute top-1/3 left-1/3 w-[400px] h-[400px] rounded-full bg-volt/3 blur-[120px]" />
        <div className="absolute bottom-1/4 right-1/4 w-[300px] h-[300px] rounded-full bg-nova/3 blur-[100px]" />
      </div>

      {/* Grid pattern overlay */}
      <div
        className="absolute inset-0 -z-10 opacity-[0.03]"
        style={{
          backgroundImage: `linear-gradient(rgba(0,212,255,0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(0,212,255,0.3) 1px, transparent 1px)`,
          backgroundSize: "60px 60px",
        }}
      />

      <div className="max-w-[1400px] mx-auto px-5 md:px-[60px]">
        {/* Eyebrow */}
        <div className="animate-fade-in mb-6">
          <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-electric/20 bg-electric/5 text-xs text-electric font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-electric animate-pulse" />
            Open Source &middot; MIT Licensed
          </span>
        </div>

        <h1 className="animate-fade-in font-heading text-5xl md:text-7xl lg:text-8xl mb-6" style={{ animationDelay: "100ms" }}>
          <span className="gradient-text">The Gravity Stack</span>
        </h1>

        <p className="animate-fade-in text-xl md:text-2xl text-dim max-w-2xl mb-4 leading-relaxed" style={{ animationDelay: "200ms" }}>
          The complete blueprint for a top 1% AI-native development environment.
        </p>

        <p className="animate-fade-in text-base text-gs-muted max-w-xl mb-12" style={{ animationDelay: "250ms" }}>
          Open source. Every tool verified in production. Every config real. Ready to fork.
        </p>

        <div className="animate-fade-in grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6 mb-12" style={{ animationDelay: "300ms" }}>
          <StatBlock value={stackStats.plugins} label="Plugins" />
          <StatBlock value={stackStats.mcpServers.display} label="MCP Servers" />
          <StatBlock value={stackStats.hooks} label="Hooks" />
          <StatBlock value={stackStats.skills} label="Skills" />
        </div>

        <div className="animate-fade-in flex flex-wrap gap-4" style={{ animationDelay: "400ms" }}>
          <a
            href="/setup"
            className="inline-flex items-center px-6 py-3 rounded-[8px] bg-electric text-bg font-medium hover:bg-electric/90 transition-all hover:shadow-[0_0_20px_rgba(0,212,255,0.3)]"
          >
            Get Started
            <svg className="ml-2 w-4 h-4" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 8h10M9 4l4 4-4 4" />
            </svg>
          </a>
          <a
            href="https://github.com/alexhale/gravity-stack"
            className="inline-flex items-center px-6 py-3 rounded-[8px] border border-gs-border text-text hover:border-electric/30 transition-all hover:bg-s1"
            target="_blank"
            rel="noopener noreferrer"
          >
            <svg className="mr-2 w-4 h-4" viewBox="0 0 16 16" fill="currentColor">
              <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z" />
            </svg>
            GitHub
          </a>
        </div>
      </div>
    </section>
  );
}

function StatBlock({ value, label }: { value: number | string; label: string }) {
  return (
    <div className="card-glow rounded-[10px] bg-s1/80 backdrop-blur-sm p-5 md:p-6 text-center">
      <div className="stat-glow font-heading text-3xl md:text-5xl text-electric mb-1">{value}</div>
      <div className="text-xs md:text-sm text-dim uppercase tracking-wider">{label}</div>
    </div>
  );
}
