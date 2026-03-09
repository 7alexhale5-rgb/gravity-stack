"use client";

import { useEffect, useState } from "react";

export function SplineHero() {
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    setIsMobile(window.innerWidth < 768 || "ontouchstart" in window);
  }, []);

  if (isMobile) return null;

  // Premium animated gradient mesh fallback (replace with Spline scene later)
  return (
    <div className="absolute inset-0 -z-10 overflow-hidden" aria-hidden="true">
      {/* Animated mesh gradient orbs */}
      <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] rounded-full bg-electric/8 blur-[120px] animate-[mesh-drift_12s_ease-in-out_infinite_alternate]" />
      <div className="absolute top-1/3 right-1/4 w-[400px] h-[400px] rounded-full bg-nova/6 blur-[100px] animate-[mesh-drift_15s_ease-in-out_infinite_alternate-reverse]" />
      <div className="absolute bottom-1/4 left-1/3 w-[350px] h-[350px] rounded-full bg-volt/4 blur-[110px] animate-[mesh-drift_10s_ease-in-out_infinite_alternate]" />

      {/* Floating particles */}
      {Array.from({ length: 8 }).map((_, i) => (
        <div
          key={i}
          className="absolute w-1 h-1 rounded-full bg-electric/40"
          style={{
            left: `${15 + i * 10}%`,
            bottom: "10%",
            animation: `float-up ${8 + i * 2}s linear infinite`,
            animationDelay: `${i * 1.5}s`,
          }}
        />
      ))}
    </div>
  );
}
