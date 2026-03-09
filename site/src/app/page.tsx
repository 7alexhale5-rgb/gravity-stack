import { Hero } from "@/components/Hero";
import { GlowCard } from "@/components/GlowCard";
import { ScrollReveal } from "@/components/ScrollReveal";
import { SectionDivider } from "@/components/SectionDivider";
import { MagneticButton } from "@/components/MagneticButton";
import { GlowEffect } from "@/components/GlowEffect";
import Link from "next/link";

const features = [
  {
    title: "31 Plugins",
    description:
      "Curated plugin collection covering code review, testing, deployment, design, security, and more. Every one verified in production.",
    href: "/plugins",
    color: "text-electric",
    glowColor: "rgba(0, 255, 136, 0.12)",
    icon: "M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5",
  },
  {
    title: "7+3 MCP Servers",
    description:
      "Connect Claude to browsers, search engines, knowledge bases, memory stores, and communication platforms.",
    href: "/mcp-servers",
    color: "text-volt",
    glowColor: "rgba(34, 197, 94, 0.10)",
    icon: "M5 12h14M12 5v14M8.5 8.5L15.5 15.5M15.5 8.5L8.5 15.5",
  },
  {
    title: "7 Lifecycle Hooks",
    description:
      "Automated guardrails: commit gates, file guards, session backup, auto-lint, context injection. Every commit type-safe.",
    href: "/hooks",
    color: "text-heat",
    glowColor: "rgba(255, 68, 68, 0.10)",
    icon: "M13 10V3L4 14h7v7l9-11h-7z",
  },
  {
    title: "53 Skills",
    description:
      "Reusable prompt templates for planning, development, research, design, management, and business workflows.",
    href: "/skills",
    color: "text-nova",
    glowColor: "rgba(255, 136, 0, 0.10)",
    icon: "M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z",
  },
  {
    title: "CARL Engine",
    description:
      "1,073-line governance engine. Context brackets, domain rules, planning router, model routing, cost management.",
    href: "/carl",
    color: "text-glow",
    glowColor: "rgba(0, 255, 136, 0.10)",
    icon: "M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z",
  },
  {
    title: "Agent Teams",
    description:
      "5 specialized roles — Architect, Implementer, Researcher, Reviewer, Tester — with model-tier routing.",
    href: "/agents",
    color: "text-ice",
    glowColor: "rgba(0, 255, 136, 0.10)",
    icon: "M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z",
  },
];

const differentiators = [
  {
    text: "Every tool is verified and running in production",
    detail: "No theoretical recommendations",
  },
  {
    text: "Every version number is pinned and tested",
    detail: "Not \"just install the latest\"",
  },
  {
    text: "Every configuration is the actual config",
    detail: "Not a sanitized example",
  },
  {
    text: "Every workflow documented from real usage",
    detail: "Not hypothetical patterns",
  },
];

export default function HomePage() {
  return (
    <>
      <Hero />

      {/* What's Inside */}
      <section className="max-w-[1400px] mx-auto px-5 md:px-[60px] py-16 md:py-24">
        <ScrollReveal>
          <h2 className="font-heading text-3xl md:text-4xl text-text mb-4">
            What&apos;s Inside
          </h2>
          <p className="text-dim mb-12 max-w-2xl">
            A complete, production-verified AI-native development environment. Not a list of links — a documented, working system.
          </p>
        </ScrollReveal>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, i) => (
            <ScrollReveal key={feature.href} delay={i * 0.08}>
              <Link href={feature.href}>
                <GlowCard className="h-full group cursor-pointer" glowColor={feature.glowColor}>
                  <div className="flex items-start gap-3">
                    <div className="relative">
                      <svg
                        className={`w-5 h-5 mt-0.5 flex-shrink-0 ${feature.color} opacity-70 group-hover:opacity-100 transition-opacity`}
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="1.5"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      >
                        <path d={feature.icon} />
                      </svg>
                      {/* Icon glow */}
                      <div
                        className="absolute inset-0 blur-[8px] opacity-0 group-hover:opacity-50 transition-opacity"
                        style={{ color: feature.glowColor }}
                      />
                    </div>
                    <div>
                      <h3 className={`font-medium text-lg mb-2 ${feature.color}`}>
                        {feature.title}
                      </h3>
                      <p className="text-sm text-dim">{feature.description}</p>
                    </div>
                  </div>
                </GlowCard>
              </Link>
            </ScrollReveal>
          ))}
        </div>
      </section>

      <SectionDivider />

      {/* Why This Stack */}
      <section className="relative overflow-hidden">
        <GlowEffect color="bg-electric/3" size="w-[500px] h-[300px]" blur="blur-[120px]" position="absolute -top-20 -right-40" />
        <div className="max-w-[1400px] mx-auto px-5 md:px-[60px] py-16 md:py-24">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-start">
            <ScrollReveal>
              <h2 className="font-heading text-3xl md:text-4xl text-text mb-4">
                Not Another Awesome List
              </h2>
              <p className="text-dim mb-6 leading-relaxed">
                Most Claude Code setups use 2-3 plugins and zero hooks. That&apos;s like
                buying a Ferrari and driving it in first gear. The Gravity Stack documents
                the full potential.
              </p>
              <Link
                href="/manifesto"
                className="text-electric text-sm hover:underline underline-offset-4"
              >
                Read the manifesto &rarr;
              </Link>
            </ScrollReveal>
            <ScrollReveal delay={0.2}>
              <div className="space-y-3">
                {differentiators.map((d, i) => (
                  <ScrollReveal key={d.text} delay={0.1 * i}>
                    <div className="flex gap-3 items-start">
                      <svg className="w-5 h-5 text-electric flex-shrink-0 mt-0.5" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                      <div>
                        <span className="text-text text-sm">{d.text}</span>
                        <span className="text-dim text-sm"> — {d.detail}</span>
                      </div>
                    </div>
                  </ScrollReveal>
                ))}
              </div>
            </ScrollReveal>
          </div>
        </div>
      </section>

      <SectionDivider />

      {/* CTA */}
      <section className="relative overflow-hidden">
        <GlowEffect color="bg-nova/4" size="w-[400px] h-[300px]" blur="blur-[130px]" position="absolute top-1/2 left-1/4 -translate-y-1/2" />
        <GlowEffect color="bg-electric/3" size="w-[300px] h-[200px]" blur="blur-[100px]" position="absolute bottom-0 right-1/4" />
        <div className="max-w-[1400px] mx-auto px-5 md:px-[60px] py-16 md:py-24">
          <ScrollReveal>
            <div className="text-center">
              <h2 className="font-heading text-3xl md:text-4xl text-text mb-4">
                Ready to Build?
              </h2>
              <p className="text-dim mb-8 max-w-xl mx-auto">
                Clone the repo, run the toolkit, and have a production-grade AI-native
                environment in minutes.
              </p>
              <div className="flex justify-center gap-4">
                <MagneticButton>
                  <Link
                    href="/setup"
                    className="inline-flex items-center px-7 py-3.5 rounded-[10px] bg-electric text-bg font-medium hover:bg-electric/90 transition-all hover:shadow-[0_0_30px_rgba(0,255,136,0.4)]"
                  >
                    Setup Guide
                  </Link>
                </MagneticButton>
                <MagneticButton>
                  <Link
                    href="/manifesto"
                    className="inline-flex items-center px-7 py-3.5 rounded-[10px] border border-gs-border text-text hover:border-electric/30 transition-colors hover:bg-s1"
                  >
                    Read the Manifesto
                  </Link>
                </MagneticButton>
              </div>
            </div>
          </ScrollReveal>
        </div>
      </section>
    </>
  );
}
