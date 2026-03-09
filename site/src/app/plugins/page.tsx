import { plugins, pluginCategories } from "@/lib/data/plugins";
import { PluginCard } from "@/components/PluginCard";
import { Badge } from "@/components/Badge";
import { PageHeader } from "@/components/PageHeader";
import { ScrollReveal } from "@/components/ScrollReveal";

export const metadata = {
  title: "Plugins",
  description: "31 verified plugins organized by category. Every one running in production.",
};

export default function PluginsPage() {
  return (
    <div className="max-w-[1400px] mx-auto px-5 md:px-[60px] py-16 md:py-24">
      <PageHeader
        eyebrow="Layer 1 — Intelligence"
        title="Plugin Encyclopedia"
        description={`31 plugins organized into ${pluginCategories.length} categories. Each extends Claude Code with specialized skills, tools, and workflows.`}
      />
      <p className="text-sm text-dim mb-12 -mt-8">
        Plugins load on-demand — having 31 enabled doesn&apos;t slow startup.
      </p>

      <ScrollReveal>
        <div className="flex flex-wrap gap-2 mb-8">
          {pluginCategories.map((cat) => (
            <Badge key={cat} variant={cat}>
              {cat} ({plugins.filter((p) => p.category === cat).length})
            </Badge>
          ))}
        </div>
      </ScrollReveal>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {plugins.map((plugin, i) => (
          <ScrollReveal key={plugin.id} delay={i * 0.04}>
            <PluginCard plugin={plugin} />
          </ScrollReveal>
        ))}
      </div>
    </div>
  );
}
