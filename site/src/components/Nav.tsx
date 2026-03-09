import Link from "next/link";
import { ActiveLink } from "./ActiveLink";
import { MobileMenu } from "./MobileMenu";
import { SearchTrigger } from "./SearchDialog";

const links = [
  { href: "/", label: "Home" },
  { href: "/manifesto", label: "Manifesto" },
  { href: "/stack", label: "Stack" },
  { href: "/plugins", label: "Plugins" },
  { href: "/mcp-servers", label: "MCP" },
  { href: "/hooks", label: "Hooks" },
  { href: "/carl", label: "CARL" },
  { href: "/skills", label: "Skills" },
  { href: "/agents", label: "Agents" },
  { href: "/architecture", label: "Architecture" },
  { href: "/setup", label: "Setup" },
  { href: "/roadmap", label: "Roadmap" },
];

export function Nav() {
  return (
    <nav className="sticky top-0 z-50 backdrop-blur-[16px] bg-bg/70 border-b border-gs-border/50 transition-all duration-300">
      {/* Bottom glow line */}
      <div className="absolute bottom-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-electric/20 to-transparent" aria-hidden="true" />

      <div className="max-w-[1400px] mx-auto px-5 md:px-[60px] flex items-center justify-between h-14">
        <Link href="/" className="font-heading text-xl text-electric hover:text-electric/80 transition-colors relative group">
          Gravity Stack
          {/* Logo glow */}
          <span className="absolute -inset-2 bg-electric/5 rounded-lg blur-sm opacity-0 group-hover:opacity-100 transition-opacity" aria-hidden="true" />
        </Link>
        <div className="hidden lg:flex items-center gap-5">
          {links.slice(1).map((link) => (
            <ActiveLink key={link.href} href={link.href}>
              {link.label}
            </ActiveLink>
          ))}
          <SearchTrigger />
        </div>
        <MobileMenu links={links} />
      </div>
    </nav>
  );
}
