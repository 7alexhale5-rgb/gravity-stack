import type { Hook } from "@/lib/data/hooks";
import { Card } from "./Card";
import { Badge } from "./Badge";
import { CodeBlock } from "./CodeBlock";

export function HookCard({ hook }: { hook: Hook }) {
  return (
    <Card className="space-y-4">
      <div className="flex items-start justify-between">
        <h3 className="font-medium text-text">{hook.name}</h3>
        <div className="flex gap-2">
          <Badge variant="core">{hook.event}</Badge>
          {hook.matcher && <Badge variant="development">{hook.matcher}</Badge>}
        </div>
      </div>
      <p className="text-sm text-dim">{hook.description}</p>
      <CodeBlock code={hook.code} language={hook.language} />
      <p className="text-xs text-gs-muted italic">{hook.why}</p>
    </Card>
  );
}
