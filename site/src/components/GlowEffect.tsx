import { cn } from "@/lib/utils";

interface GlowEffectProps {
  color?: string;
  size?: string;
  blur?: string;
  position?: string;
  animate?: boolean;
  className?: string;
}

export function GlowEffect({
  color = "bg-electric/5",
  size = "w-[600px] h-[400px]",
  blur = "blur-[150px]",
  position = "top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2",
  animate = false,
  className,
}: GlowEffectProps) {
  return (
    <div
      className={cn(
        "absolute rounded-full pointer-events-none",
        color,
        size,
        blur,
        position,
        animate && "animate-glow-drift",
        className
      )}
      aria-hidden="true"
    />
  );
}
