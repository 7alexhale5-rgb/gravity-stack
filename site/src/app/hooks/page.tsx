import { hooks } from "@/lib/data/hooks";
import { HookCard } from "@/components/HookCard";
import { Callout } from "@/components/Callout";

export const metadata = {
  title: "Lifecycle Hooks — Gravity Stack",
  description: "7 lifecycle hooks providing automated guardrails, context injection, and governance.",
};

export default function HooksPage() {
  return (
    <div className="max-w-[1400px] mx-auto px-5 md:px-[60px] py-16 md:py-24">
      <h1 className="font-heading text-4xl md:text-6xl mb-6">
        <span className="gradient-text">Lifecycle Hooks</span>
      </h1>
      <p className="text-xl text-dim max-w-2xl mb-8">
        Hooks are shell commands that execute automatically in response to Claude
        Code lifecycle events. They run before or after specific actions, enabling
        guardrails, automation, and context injection.
      </p>

      <Callout variant="tip" title="How hooks work">
        Hooks are configured in <code className="font-mono text-xs bg-s2 px-1.5 py-0.5 rounded">~/.claude/settings.json</code>.
        Each hook specifies an event, an optional matcher (to filter which tool triggers it),
        and a command to run. Exit code 0 = allow, exit code 2 = block.
      </Callout>

      <div className="space-y-8 mt-12">
        {hooks.map((hook) => (
          <HookCard key={hook.name} hook={hook} />
        ))}
      </div>
    </div>
  );
}
