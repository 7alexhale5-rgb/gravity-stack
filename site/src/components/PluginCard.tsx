import type { Plugin } from "@/lib/data/plugins";
import { Card } from "./Card";
import { Badge } from "./Badge";

export function PluginCard({ plugin }: { plugin: Plugin }) {
  return (
    <Card>
      <div className="flex items-start justify-between mb-3">
        <h3 className="font-medium text-text">{plugin.name}</h3>
        <Badge variant={plugin.priority}>{plugin.priority}</Badge>
      </div>
      <p className="text-sm text-dim mb-4 line-clamp-3">{plugin.description}</p>
      <div className="flex items-center gap-2">
        <Badge variant={plugin.category}>{plugin.category}</Badge>
        <span className="text-xs text-gs-muted">{plugin.publisher}</span>
      </div>
    </Card>
  );
}
