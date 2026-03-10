"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

export function ActiveLink({
  href,
  children,
  className,
}: {
  href: string;
  children: React.ReactNode;
  className?: string;
}) {
  const pathname = usePathname();
  const isActive = href === "/" ? pathname === "/" : pathname.startsWith(href);

  return (
    <Link
      href={href}
      className={cn(
        "relative text-sm transition-colors py-1",
        isActive ? "text-electric" : "text-dim hover:text-text",
        className
      )}
    >
      {children}
      {isActive && (
        <span
          className="absolute -bottom-[17px] left-1/2 -translate-x-1/2 w-1 h-1 rounded-full bg-electric shadow-[0_0_6px_rgba(0,255,136,0.6)]"
          aria-hidden="true"
        />
      )}
    </Link>
  );
}
