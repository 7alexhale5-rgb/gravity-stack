import { cn } from "@/lib/utils";

export function Card({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "card-glow rounded-[10px] bg-s1 p-6 transition-all duration-200",
        className
      )}
    >
      {children}
    </div>
  );
}
