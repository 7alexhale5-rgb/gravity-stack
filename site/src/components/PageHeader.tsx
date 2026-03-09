"use client";

import { motion } from "framer-motion";
import { TextReveal } from "./TextReveal";
import { GlowEffect } from "./GlowEffect";

export function PageHeader({
  title,
  description,
  eyebrow,
}: {
  title: string;
  description: string;
  eyebrow?: string;
}) {
  return (
    <div className="relative mb-12">
      {/* Subtle glow behind title */}
      <GlowEffect
        color="bg-electric/3"
        size="w-[400px] h-[200px]"
        blur="blur-[100px]"
        position="absolute -top-20 -left-20"
      />

      {eyebrow && (
        <motion.p
          className="text-sm text-electric font-mono mb-3 uppercase tracking-wider"
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.4 }}
        >
          {eyebrow}
        </motion.p>
      )}
      <h1 className="font-heading text-4xl md:text-6xl mb-4">
        <TextReveal text={title} gradient delay={0.1} />
      </h1>
      <motion.p
        className="text-xl text-dim max-w-2xl leading-relaxed"
        initial={{ opacity: 0, filter: "blur(4px)" }}
        animate={{ opacity: 1, filter: "blur(0px)" }}
        transition={{ duration: 0.6, delay: 0.4 }}
      >
        {description}
      </motion.p>
    </div>
  );
}
