import { cn } from "@/lib/utils";

export function SectionDivider({ className }: { className?: string }) {
  return (
    <div className={cn("section-divider", className)} aria-hidden="true" />
  );
}
