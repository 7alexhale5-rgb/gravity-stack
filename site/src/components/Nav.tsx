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
    <nav className="sticky top-0 z-50 backdrop-blur-[12px] bg-bg/80 border-b border-gs-border">
      <div className="max-w-[1400px] mx-auto px-5 md:px-[60px] flex items-center justify-between h-14">
        <Link href="/" className="font-heading text-xl text-electric">
          Gravity Stack
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
