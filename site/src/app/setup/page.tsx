import { Timeline } from "@/components/Timeline";
import { Card } from "@/components/Card";
import { CodeBlock } from "@/components/CodeBlock";
import { Callout } from "@/components/Callout";
import { ScrollReveal } from "@/components/ScrollReveal";
import { SectionDivider } from "@/components/SectionDivider";

export const metadata = {
  title: "Setup Guide",
  description: "Step-by-step installation guide for the Gravity Stack AI-native development environment.",
};

const prerequisites = [
  { requirement: "macOS", minimum: "Ventura 13.0+", recommended: "Sequoia 15.0+" },
  { requirement: "Architecture", minimum: "Apple Silicon (M1+)", recommended: "M2 Pro / M3+" },
  { requirement: "Node.js", minimum: "20.9", recommended: "22 LTS" },
  { requirement: "Python", minimum: "3.10", recommended: "3.12" },
  { requirement: "Claude Code", minimum: "Latest", recommended: "Latest" },
  { requirement: "Subscription", minimum: "Claude Pro", recommended: "Claude Max" },
  { requirement: "Disk space", minimum: "2 GB", recommended: "5 GB" },
];

const setupSteps = [
  {
    title: "Clone the Repository",
    description: "Get the Gravity Stack source code and navigate to the toolkit directory.",
  },
  {
    title: "Run the Installer",
    description: "The master bootstrap script checks prerequisites and runs all 5 phases automatically.",
  },
  {
    title: "Foundation",
    description: "Installs Xcode CLT, Homebrew, Node.js 22 (nvm), Python 3.12 (pyenv), Docker, Git, and gh CLI.",
  },
  {
    title: "Claude Code Setup",
    description: "Installs the CLI, creates directory structure (~/.claude/hooks, memory, backups), copies settings.",
  },
  {
    title: "MCP Servers",
    description: "Configures Playwright, Firecrawl, Perplexity, Memory, and Hacker News MCP servers.",
  },
  {
    title: "Hooks",
    description: "Installs commit gate, file guard, notification, session backup, auto-lint, and CARL hooks.",
  },
  {
    title: "Verification",
    description: "Runs the verification script to confirm all tools are installed and configured correctly.",
  },
];

const quickStartCode = `git clone https://github.com/alexhale/gravity-stack.git
cd gravity-stack/toolkit
chmod +x install.sh
./install.sh`;

export default function SetupPage() {
  return (
    <div className="max-w-[1400px] mx-auto px-5 md:px-[60px] py-16 md:py-24">
      <h1 className="font-heading text-4xl md:text-6xl mb-6">
        <span className="gradient-text">Setup Guide</span>
      </h1>
      <p className="text-xl text-dim max-w-2xl mb-12">
        From zero to a fully-configured AI-native development environment.
        The installer is idempotent — safe to re-run any time.
      </p>

      <ScrollReveal>
        <h2 className="font-heading text-3xl text-text mb-6">Quick Start</h2>
        <div className="mb-12">
          <CodeBlock code={quickStartCode} language="bash" />
        </div>
      </ScrollReveal>

      <SectionDivider className="mb-12" />

      <ScrollReveal>
        <h2 className="font-heading text-3xl text-text mb-6">Prerequisites</h2>
        <div className="overflow-x-auto mb-12">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gs-border">
                <th className="text-left py-3 px-4 text-dim font-medium">Requirement</th>
                <th className="text-left py-3 px-4 text-dim font-medium">Minimum</th>
                <th className="text-left py-3 px-4 text-dim font-medium">Recommended</th>
              </tr>
            </thead>
            <tbody>
              {prerequisites.map((prereq) => (
                <tr key={prereq.requirement} className="border-b border-gs-border/50">
                  <td className="py-3 px-4 text-text font-medium">{prereq.requirement}</td>
                  <td className="py-3 px-4 text-dim">{prereq.minimum}</td>
                  <td className="py-3 px-4 text-electric">{prereq.recommended}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </ScrollReveal>

      <SectionDivider className="mb-12" />

      <ScrollReveal>
        <h2 className="font-heading text-3xl text-text mb-6">Installation Steps</h2>
        <div className="mb-12">
          <Timeline steps={setupSteps} />
        </div>
      </ScrollReveal>

      <ScrollReveal delay={0.1}>
        <Callout variant="tip" title="Idempotent">
          Every script checks before installing. Safe to re-run any time.
          Will never downgrade or overwrite existing configs.
        </Callout>
      </ScrollReveal>

      <SectionDivider className="mt-12 mb-12" />

      <ScrollReveal>
        <h2 className="font-heading text-3xl text-text mb-6">
          Common Issues
        </h2>
      </ScrollReveal>
      <div className="space-y-4">
        {[
          { issue: "claude: command not found", solution: "Run npm install -g @anthropic-ai/claude-code and restart terminal" },
          { issue: "MCP server timeout", solution: "Check if the npm package version is pinned correctly" },
          { issue: "Hook permission denied", solution: "Run chmod +x ~/.claude/hooks/*.py" },
          { issue: "Node version mismatch", solution: "Run nvm use 22 or add to .nvmrc" },
        ].map((item, i) => (
          <ScrollReveal key={item.issue} delay={i * 0.06}>
            <Card className="flex flex-col md:flex-row gap-4">
              <code className="font-mono text-sm text-heat flex-shrink-0">{item.issue}</code>
              <p className="text-sm text-dim">{item.solution}</p>
            </Card>
          </ScrollReveal>
        ))}
      </div>
    </div>
  );
}
