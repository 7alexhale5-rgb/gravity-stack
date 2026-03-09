import { skills, skillCategories } from "@/lib/data/skills";
import { Card } from "@/components/Card";
import { Badge } from "@/components/Badge";
import { PageHeader } from "@/components/PageHeader";
import { ScrollReveal } from "@/components/ScrollReveal";
import { SectionDivider } from "@/components/SectionDivider";

export const metadata = {
  title: "Skills",
  description:
    "53 reusable prompt templates across 14 categories. Planning, development, testing, design, research, and more.",
};

export default function SkillsPage() {
  return (
    <div className="max-w-[1400px] mx-auto px-5 md:px-[60px] py-16 md:py-24">
      <PageHeader
        eyebrow="Layer 1 — Intelligence"
        title="Skills Encyclopedia"
        description="53 reusable prompt templates organized across 14 categories. Each skill is a slash command that triggers a specialized workflow."
      />

      <ScrollReveal>
        <div className="flex flex-wrap gap-2 mb-12">
          {skillCategories.map((cat) => (
            <Badge key={cat} variant={cat}>
              {cat} ({skills.filter((s) => s.category === cat).length})
            </Badge>
          ))}
        </div>
      </ScrollReveal>

      {skillCategories.map((category) => {
        const categorySkills = skills.filter((s) => s.category === category);
        return (
          <ScrollReveal key={category}>
            <section className="mb-12">
              <h2 className="font-heading text-2xl text-text mb-4 capitalize">
                {category}
                <span className="text-dim text-base ml-2 font-normal">
                  ({categorySkills.length})
                </span>
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {categorySkills.map((skill, i) => (
                  <ScrollReveal key={skill.command} delay={i * 0.03}>
                    <Card>
                      <div className="flex items-start justify-between gap-3 mb-2">
                        <h3 className="font-medium text-text">{skill.name}</h3>
                        <code className="text-xs font-mono text-electric bg-electric/10 px-2 py-0.5 rounded flex-shrink-0">
                          {skill.command}
                        </code>
                      </div>
                      <p className="text-sm text-dim">{skill.description}</p>
                    </Card>
                  </ScrollReveal>
                ))}
              </div>
            </section>
          </ScrollReveal>
        );
      })}
    </div>
  );
}
