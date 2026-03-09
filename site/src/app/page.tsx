import { Hero } from "@/components/Hero";
import { Card } from "@/components/Card";
import Link from "next/link";

const features = [
  {
    title: "31 Plugins",
    description:
      "Curated plugin collection covering code review, testing, deployment, design, security, and more. Every one verified in production.",
    href: "/plugins",
    color: "text-electric",
  },
  {
    title: "9+3 MCP Servers",
    description:
      "Connect Claude to browsers, search engines, knowledge bases, memory stores, and communication platforms.",
    href: "/mcp-servers",
    color: "text-volt",
  },
  {
    title: "7 Lifecycle Hooks",
    description:
      "Automated guardrails: commit gates, file guards, session backup, auto-lint, context injection. Every commit type-safe.",
    href: "/hooks",
    color: "text-heat",
  },
  {
    title: "53 Skills",
    description:
      "Reusable prompt templates for planning, development, research, design, management, and business workflows.",
    href: "/stack",
    color: "text-nova",
  },
  {
    title: "CARL Engine",
    description:
      "1,073-line governance engine. Context brackets, domain rules, planning router, model routing, cost management.",
    href: "/carl",
    color: "text-glow",
  },
  {
    title: "Agent Teams",
    description:
      "5 specialized roles — Architect, Implementer, Researcher, Reviewer, Tester — with model-tier routing.",
    href: "/agents",
    color: "text-ice",
  },
];

export default function HomePage() {
  return (
    <>
      <Hero />
      <section className="max-w-[1400px] mx-auto px-5 md:px-[60px] py-16 md:py-24">
        <h2 className="font-heading text-3xl md:text-4xl text-text mb-4">
          What&apos;s Inside
        </h2>
        <p className="text-dim mb-12 max-w-2xl">
          Every tool verified and running in production. Every version pinned and tested.
          Every configuration is the actual config — not a sanitized example.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature) => (
            <Link key={feature.href} href={feature.href}>
              <Card className="h-full hover:bg-s2 transition-colors">
                <h3 className={`font-medium text-lg mb-2 ${feature.color}`}>
                  {feature.title}
                </h3>
                <p className="text-sm text-dim">{feature.description}</p>
              </Card>
            </Link>
          ))}
        </div>
      </section>

      <section className="max-w-[1400px] mx-auto px-5 md:px-[60px] py-16 border-t border-gs-border">
        <div className="text-center">
          <h2 className="font-heading text-3xl md:text-4xl text-text mb-4">
            Ready to Build?
          </h2>
          <p className="text-dim mb-8 max-w-xl mx-auto">
            Clone the repo, run the toolkit, and have a production-grade AI-native
            environment in minutes.
          </p>
          <div className="flex justify-center gap-4">
            <Link
              href="/setup"
              className="inline-flex items-center px-6 py-3 rounded-[8px] bg-electric text-bg font-medium hover:bg-electric/90 transition-colors"
            >
              Setup Guide
            </Link>
            <Link
              href="/manifesto"
              className="inline-flex items-center px-6 py-3 rounded-[8px] border border-gs-border text-text hover:border-electric/30 transition-colors"
            >
              Read the Manifesto
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
