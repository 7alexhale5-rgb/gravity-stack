import { hooks } from "@/lib/data/hooks";
import { HookCard } from "@/components/HookCard";
import { Callout } from "@/components/Callout";
import { PageHeader } from "@/components/PageHeader";
import { ScrollReveal } from "@/components/ScrollReveal";
import { SectionDivider } from "@/components/SectionDivider";

export const metadata = {
  title: "Lifecycle Hooks",
  description: "7 lifecycle hooks providing automated guardrails, context injection, and governance.",
};

export default function HooksPage() {
  return (
    <div className="max-w-[1400px] mx-auto px-5 md:px-[60px] py-16 md:py-24">
      <PageHeader
        eyebrow="Layer 2 — Governance"
        title="Lifecycle Hooks"
        description="Hooks are shell commands that execute automatically in response to Claude Code lifecycle events. They run before or after specific actions, enabling guardrails, automation, and context injection."
      />

      <ScrollReveal>
        <Callout variant="tip" title="How hooks work">
          Hooks are configured in <code className="font-mono text-xs bg-s2 px-1.5 py-0.5 rounded">~/.claude/settings.json</code>.
          Each hook specifies an event, an optional matcher (to filter which tool triggers it),
          and a command to run. Exit code 0 = allow, exit code 2 = block.
        </Callout>
      </ScrollReveal>

      <SectionDivider className="mt-12 mb-8" />

      <div className="space-y-8">
        {hooks.map((hook, i) => (
          <ScrollReveal key={hook.name} delay={i * 0.06}>
            <HookCard hook={hook} />
          </ScrollReveal>
        ))}
      </div>
    </div>
  );
}
