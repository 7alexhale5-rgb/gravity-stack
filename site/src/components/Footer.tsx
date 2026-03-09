import Link from "next/link";

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
    <footer className="border-t border-gs-border mt-24">
      <div className="max-w-[1400px] mx-auto px-5 md:px-[60px] py-12 md:py-16">
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
                      className="text-sm text-dim hover:text-text transition-colors"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom bar */}
        <div className="flex flex-col md:flex-row items-center justify-between gap-4 pt-8 border-t border-gs-border/50">
          <p className="text-xs text-dim">
            MIT License &middot; By Alex Hale &amp; Claude
          </p>
          <div className="flex items-center gap-4">
            <a
              href="https://github.com/alexhale/gravity-stack"
              className="text-xs text-dim hover:text-text transition-colors"
              target="_blank"
              rel="noopener noreferrer"
            >
              GitHub
            </a>
            <span className="text-gs-border">&middot;</span>
            <span className="text-xs text-dim">
              Built with Next.js 16 &amp; Tailwind v4
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
}
