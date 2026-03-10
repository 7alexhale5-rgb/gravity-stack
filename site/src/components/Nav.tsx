"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { cn } from "@/lib/utils";
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
  const [scrolled, setScrolled] = useState(false);
  const [hidden, setHidden] = useState(false);
  const [lastY, setLastY] = useState(0);

  useEffect(() => {
    let ticking = false;
    const onScroll = () => {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(() => {
        const y = window.scrollY;
        setScrolled(y > 20);
        if (y > 300 && y > lastY) setHidden(true);
        else setHidden(false);
        setLastY(y);
        ticking = false;
      });
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, [lastY]);

  return (
    <nav
      className={cn(
        "sticky top-0 z-50 transition-all duration-300 border-b",
        hidden ? "-translate-y-full" : "translate-y-0",
        scrolled
          ? "backdrop-blur-[20px] bg-bg/80 border-gs-border/50 shadow-[0_4px_30px_rgba(0,0,0,0.3)]"
          : "backdrop-blur-[16px] bg-bg/70 border-transparent"
      )}
    >
      {/* Bottom glow line — intensifies on scroll */}
      <div
        className={cn(
          "absolute bottom-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-cyan/20 to-transparent transition-opacity duration-300",
          scrolled ? "opacity-100" : "opacity-40"
        )}
        aria-hidden="true"
      />

      <div className="max-w-[1400px] mx-auto px-5 md:px-[60px] flex items-center justify-between h-14">
        <Link
          href="/"
          className="font-heading text-xl text-electric hover:text-electric/80 transition-colors relative group"
        >
          Gravity Stack
          <span
            className="absolute -inset-2 bg-electric/5 rounded-lg blur-sm opacity-0 group-hover:opacity-100 transition-opacity"
            aria-hidden="true"
          />
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
