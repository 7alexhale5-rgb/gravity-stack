import { cn } from "@/lib/utils";

export function DiagramNode({
  label,
  sublabel,
  variant = "default",
  className,
}: {
  label: string;
  sublabel?: string;
  variant?: "default" | "primary" | "accent";
  className?: string;
}) {
  const colors = {
    default: "border-gs-border bg-s2 text-text",
    primary: "border-electric/30 bg-electric/5 text-electric",
    accent: "border-volt/30 bg-volt/5 text-volt",
  };

  return (
    <div
      className={cn(
        "rounded-[10px] border p-4 text-center",
        colors[variant],
        className
      )}
    >
      <div className="font-mono text-sm">{label}</div>
      {sublabel && <div className="text-xs text-dim mt-1">{sublabel}</div>}
    </div>
  );
}
