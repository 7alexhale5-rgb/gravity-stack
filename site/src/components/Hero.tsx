"use client";

import { motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import { stackStats } from "@/lib/data/stack";
import { TextReveal } from "./TextReveal";
import { MagneticButton } from "./MagneticButton";
import { SplineHero } from "./SplineHero";

function CountUp({ target, duration = 2 }: { target: number | string; duration?: number }) {
  const numTarget = typeof target === "string" ? parseInt(target) || 0 : target;
  const [count, setCount] = useState(0);
  const ref = useRef<HTMLSpanElement>(null);
  const [hasAnimated, setHasAnimated] = useState(false);

  useEffect(() => {
    if (hasAnimated) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setHasAnimated(true);
          const start = performance.now();
          const animate = (now: number) => {
            const elapsed = now - start;
            const progress = Math.min(elapsed / (duration * 1000), 1);
            const eased = 1 - Math.pow(1 - progress, 3); // easeOutCubic
            setCount(Math.round(numTarget * eased));
            if (progress < 1) requestAnimationFrame(animate);
          };
          requestAnimationFrame(animate);
        }
      },
      { threshold: 0.5 }
    );
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, [numTarget, duration, hasAnimated]);

  const display = typeof target === "string" && target.includes("+")
    ? `${count}+${target.split("+").slice(1).join("+")}`
    : count;

  return <span ref={ref}>{display}</span>;
}

export function Hero() {
  return (
    <section className="relative overflow-hidden py-28 md:py-40">
      {/* 3D / Gradient mesh background */}
      <SplineHero />

      {/* Layered glow background */}
      <div className="absolute inset-0 -z-10" aria-hidden="true">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[600px] rounded-full bg-electric/5 blur-[150px]" />
        <div className="absolute top-1/3 left-1/3 w-[400px] h-[400px] rounded-full bg-volt/3 blur-[120px]" />
        <div className="absolute bottom-1/4 right-1/4 w-[300px] h-[300px] rounded-full bg-nova/3 blur-[100px]" />
      </div>

      {/* Animated grid pattern */}
      <div
        className="absolute inset-0 -z-10 animate-[grid-pulse_8s_ease-in-out_infinite]"
        style={{
          backgroundImage: `linear-gradient(rgba(0,212,255,0.15) 1px, transparent 1px), linear-gradient(90deg, rgba(0,212,255,0.15) 1px, transparent 1px)`,
          backgroundSize: "60px 60px",
          maskImage: "radial-gradient(ellipse at center, black 30%, transparent 70%)",
          WebkitMaskImage: "radial-gradient(ellipse at center, black 30%, transparent 70%)",
        }}
        aria-hidden="true"
      />

      <div className="max-w-[1400px] mx-auto px-5 md:px-[60px]">
        {/* Eyebrow with shimmer border */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-8"
        >
          <span
            className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs text-electric font-medium"
            style={{
              background: "rgba(0, 212, 255, 0.06)",
              border: "1px solid rgba(0, 212, 255, 0.15)",
              backgroundSize: "200% 100%",
              animation: "border-shimmer 3s ease-in-out infinite",
            }}
          >
            <span className="w-1.5 h-1.5 rounded-full bg-electric animate-pulse" />
            Open Source &middot; MIT Licensed
          </span>
        </motion.div>

        {/* Title with character reveal */}
        <h1 className="font-heading text-5xl md:text-7xl lg:text-8xl mb-6">
          <TextReveal text="The Gravity Stack" gradient delay={0.2} />
        </h1>

        {/* Subtitle with blur-in effect */}
        <motion.p
          className="text-xl md:text-2xl text-dim max-w-2xl mb-4 leading-relaxed"
          initial={{ opacity: 0, filter: "blur(8px)" }}
          animate={{ opacity: 1, filter: "blur(0px)" }}
          transition={{ duration: 0.8, delay: 0.6 }}
        >
          The complete blueprint for a top 1% AI-native development environment.
        </motion.p>

        <motion.p
          className="text-base text-gs-muted max-w-xl mb-14"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.8 }}
        >
          Open source. Every tool verified in production. Every config real. Ready to fork.
        </motion.p>

        {/* Stats with glass cards and count-up */}
        <motion.div
          className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6 mb-14"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 1.0 }}
        >
          <StatBlock value={stackStats.plugins} label="Plugins" />
          <StatBlock value={stackStats.mcpServers.display} label="MCP Servers" />
          <StatBlock value={stackStats.hooks} label="Hooks" />
          <StatBlock value={stackStats.skills} label="Skills" />
        </motion.div>

        {/* CTAs with magnetic effect */}
        <motion.div
          className="flex flex-wrap gap-4"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 1.2 }}
        >
          <MagneticButton>
            <a
              href="/setup"
              className="inline-flex items-center px-7 py-3.5 rounded-[10px] bg-electric text-bg font-medium hover:bg-electric/90 transition-all hover:shadow-[0_0_30px_rgba(0,212,255,0.4)] text-sm"
            >
              Get Started
              <svg className="ml-2 w-4 h-4" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M3 8h10M9 4l4 4-4 4" />
              </svg>
            </a>
          </MagneticButton>
          <MagneticButton>
            <a
              href="https://github.com/alexhale/gravity-stack"
              className="inline-flex items-center px-7 py-3.5 rounded-[10px] border border-gs-border text-text hover:border-electric/30 transition-all hover:bg-s1 text-sm"
              target="_blank"
              rel="noopener noreferrer"
            >
              <svg className="mr-2 w-4 h-4" viewBox="0 0 16 16" fill="currentColor">
                <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z" />
              </svg>
              GitHub
            </a>
          </MagneticButton>
        </motion.div>
      </div>
    </section>
  );
}

function StatBlock({ value, label }: { value: number | string; label: string }) {
  return (
    <div className="glass rounded-[10px] p-5 md:p-6 text-center group hover:border-electric/20 transition-all duration-300 hover:translate-y-[-2px]">
      <div className="stat-glow font-heading text-3xl md:text-5xl text-electric mb-1">
        <CountUp target={value} />
      </div>
      <div className="text-xs md:text-sm text-dim uppercase tracking-wider">{label}</div>
    </div>
  );
}
