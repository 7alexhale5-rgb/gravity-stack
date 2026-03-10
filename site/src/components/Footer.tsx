import Link from "next/link";
import { GlowEffect } from "./GlowEffect";

const navGroups = [
  {
    title: "Learn",
    links: [
      { href: "/manifesto", label: "Manifesto" },
      { href: "/stack", label: "The Stack" },
      { href: "/architecture", label: "Architecture" },
      { href: "/setup", label: "Setup Guide" },
    ],
  },
  {
    title: "Components",
    links: [
      { href: "/plugins", label: "Plugins" },
      { href: "/mcp-servers", label: "MCP Servers" },
      { href: "/hooks", label: "Hooks" },
      { href: "/carl", label: "CARL Engine" },
      { href: "/skills", label: "Skills" },
    ],
  },
  {
    title: "Teams",
    links: [
      { href: "/agents", label: "Agent Teams" },
      { href: "/roadmap", label: "Roadmap" },
    ],
  },
];

export function Footer() {
  return (
    <footer className="relative z-[2] mt-24 overflow-hidden">
      {/* Gradient divider at top */}
      <div className="h-[1px] bg-gradient-to-r from-transparent via-cyan/20 to-transparent" aria-hidden="true" />

      {/* Ambient glow */}
      <GlowEffect color="bg-electric/2" size="w-[400px] h-[200px]" blur="blur-[120px]" position="absolute -bottom-20 left-1/4" />
      <GlowEffect color="bg-nova/2" size="w-[300px] h-[150px]" blur="blur-[100px]" position="absolute -bottom-10 right-1/3" />

      <div className="max-w-[1400px] mx-auto px-5 md:px-[60px] py-12 md:py-16 relative">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-12">
          {/* Brand */}
          <div className="col-span-2 md:col-span-1">
            <Link href="/" className="font-heading text-xl text-electric">
              Gravity Stack
            </Link>
            <p className="text-sm text-dim mt-3 max-w-[240px]">
              The complete blueprint for a top 1% AI-native development environment.
            </p>
          </div>

          {/* Nav groups */}
          {navGroups.map((group) => (
            <div key={group.title}>
              <h3 className="text-sm font-medium text-text mb-3">{group.title}</h3>
              <ul className="space-y-2">
                {group.links.map((link) => (
                  <li key={link.href}>
                    <Link
                      href={link.href}
                      className="text-sm text-dim hover:text-electric transition-colors inline-flex items-center gap-1 group"
                    >
                      {link.label}
                      <svg
                        className="w-3 h-3 opacity-0 -translate-x-1 group-hover:opacity-100 group-hover:translate-x-0 transition-all duration-200"
                        viewBox="0 0 16 16"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                      >
                        <path d="M6 4l4 4-4 4" />
                      </svg>
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom bar */}
        <div className="flex flex-col md:flex-row items-center justify-between gap-4 pt-8 border-t border-gs-border/30">
          <p className="text-xs text-dim">
            MIT License &middot; By Alex Hale &amp; Claude
          </p>
          <div className="flex items-center gap-5">
            <a
              href="https://github.com/7alexhale5-rgb/gravity-stack"
              className="text-dim hover:text-electric transition-colors group"
              target="_blank"
              rel="noopener noreferrer"
              aria-label="GitHub"
            >
              <svg className="w-4 h-4 group-hover:drop-shadow-[0_0_6px_rgba(0,255,136,0.4)]" viewBox="0 0 16 16" fill="currentColor">
                <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z" />
              </svg>
            </a>
            <a
              href="https://x.com"
              className="text-dim hover:text-electric transition-colors group"
              target="_blank"
              rel="noopener noreferrer"
              aria-label="X (Twitter)"
            >
              <svg className="w-4 h-4 group-hover:drop-shadow-[0_0_6px_rgba(0,255,136,0.4)]" viewBox="0 0 24 24" fill="currentColor">
                <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
              </svg>
            </a>
            <span className="text-gs-border/50">&middot;</span>
            <span className="text-xs text-dim">
              Next.js 16 &middot; Tailwind v4
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
}
