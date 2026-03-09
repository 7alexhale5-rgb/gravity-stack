import { cn } from "@/lib/utils";

const variants = {
  core: "bg-electric/10 text-electric border-electric/20",
  development: "bg-volt/10 text-volt border-volt/20",
  testing: "bg-heat/10 text-heat border-heat/20",
  integration: "bg-nova/10 text-nova border-nova/20",
  deployment: "bg-glow/10 text-glow border-glow/20",
  research: "bg-ice/10 text-ice border-ice/20",
  design: "bg-nova/10 text-nova border-nova/20",
  review: "bg-electric/10 text-electric border-electric/20",
  custom: "bg-dim/10 text-dim border-dim/20",
  essential: "bg-electric/10 text-electric border-electric/20",
  recommended: "bg-volt/10 text-volt border-volt/20",
  optional: "bg-dim/10 text-dim border-dim/20",
  planning: "bg-electric/10 text-electric border-electric/20",
  management: "bg-glow/10 text-glow border-glow/20",
  governance: "bg-heat/10 text-heat border-heat/20",
  writing: "bg-ice/10 text-ice border-ice/20",
  business: "bg-glow/10 text-glow border-glow/20",
  utility: "bg-dim/10 text-dim border-dim/20",
  frontend: "bg-volt/10 text-volt border-volt/20",
  advanced: "bg-nova/10 text-nova border-nova/20",
  content: "bg-ice/10 text-ice border-ice/20",
  debugging: "bg-heat/10 text-heat border-heat/20",
  high: "bg-electric/10 text-electric border-electric/20",
  medium: "bg-glow/10 text-glow border-glow/20",
  npm: "bg-volt/10 text-volt border-volt/20",
  sse: "bg-nova/10 text-nova border-nova/20",
  cloud: "bg-ice/10 text-ice border-ice/20",
} as const;

export function Badge({
  variant,
  children,
}: {
  variant: keyof typeof variants;
  children: React.ReactNode;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center px-2.5 py-0.5 rounded-[6px] text-xs font-medium border transition-colors cursor-default badge-shimmer",
        variants[variant] || variants.custom
      )}
    >
      {children}
    </span>
  );
}
