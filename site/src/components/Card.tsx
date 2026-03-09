import { cn } from "@/lib/utils";

type CardVariant = "default" | "glass" | "glow";

interface CardProps {
  children: React.ReactNode;
  className?: string;
  variant?: CardVariant;
}

const variantStyles: Record<CardVariant, string> = {
  default: "card-glow bg-s1",
  glass: "glass bg-s1/40",
  glow: "glow-border bg-s1/60 glass",
};

export function Card({ children, className, variant = "default" }: CardProps) {
  return (
    <div
      className={cn(
        "rounded-[10px] p-6 transition-all duration-300",
        variantStyles[variant],
        className
      )}
    >
      {children}
    </div>
  );
}
