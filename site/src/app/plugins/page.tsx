import { plugins, pluginCategories } from "@/lib/data/plugins";
import { PluginCard } from "@/components/PluginCard";
import { Badge } from "@/components/Badge";

export const metadata = {
  title: "Plugins — Gravity Stack",
  description: "31 verified plugins organized by category. Every one running in production.",
};

export default function PluginsPage() {
  return (
    <div className="max-w-[1400px] mx-auto px-5 md:px-[60px] py-16 md:py-24">
      <h1 className="font-heading text-4xl md:text-6xl mb-6">
        <span className="gradient-text">Plugin Encyclopedia</span>
      </h1>
      <p className="text-xl text-dim max-w-2xl mb-4">
        31 plugins organized into {pluginCategories.length} categories. Each extends Claude
        Code with specialized skills, tools, and workflows.
      </p>
      <p className="text-sm text-dim mb-12">
        Plugins load on-demand — having 31 enabled doesn&apos;t slow startup.
      </p>

      <div className="flex flex-wrap gap-2 mb-8">
        {pluginCategories.map((cat) => (
          <Badge key={cat} variant={cat}>
            {cat} ({plugins.filter((p) => p.category === cat).length})
          </Badge>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {plugins.map((plugin) => (
          <PluginCard key={plugin.id} plugin={plugin} />
        ))}
      </div>
    </div>
  );
}
