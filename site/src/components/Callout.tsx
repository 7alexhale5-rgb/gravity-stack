import { cn } from "@/lib/utils";

const variants = {
  info: {
    border: "border-l-electric",
    bg: "bg-electric/5",
    icon: "i",
  },
  warning: {
    border: "border-l-glow",
    bg: "bg-glow/5",
    icon: "!",
  },
  tip: {
    border: "border-l-volt",
    bg: "bg-volt/5",
    icon: "\u2726",
  },
};

export function Callout({
  variant = "info",
  title,
  children,
}: {
  variant?: keyof typeof variants;
  title?: string;
  children: React.ReactNode;
}) {
  const v = variants[variant];
  return (
    <div className={cn("border-l-4 rounded-r-[10px] p-4", v.border, v.bg)}>
      {title && (
        <div className="flex items-center gap-2 mb-2">
          <span className="text-sm font-medium text-text">{v.icon}</span>
          <span className="text-sm font-medium text-text">{title}</span>
        </div>
      )}
      <div className="text-sm text-dim">{children}</div>
    </div>
  );
}
