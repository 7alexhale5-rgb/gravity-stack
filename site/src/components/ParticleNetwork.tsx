"use client";

import { useEffect, useRef } from "react";

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
}

// Config — tuned to match the Vanta.js NET feel from Mission Control
const PARTICLE_COUNT = 60;
const MAX_DIST = 150;
const MAX_DIST_SQ = MAX_DIST * MAX_DIST;
const MOUSE_RADIUS = 200;
const MOUSE_RADIUS_SQ = MOUSE_RADIUS * MOUSE_RADIUS;
const COLOR = "0, 212, 255"; // cyan accent

function startAnimation(canvas: HTMLCanvasElement, ctx: CanvasRenderingContext2D) {
  let mouseX = -1000;
  let mouseY = -1000;
  let frameId: number;
  const particles: Particle[] = [];

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }

  function seed() {
    particles.length = 0;
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.5,
        vy: (Math.random() - 0.5) * 0.5,
      });
    }
  }

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Update positions
    for (const p of particles) {
      const dx = mouseX - p.x;
      const dy = mouseY - p.y;
      const dSq = dx * dx + dy * dy;

      // Mouse attraction (soft pull toward cursor)
      if (dSq < MOUSE_RADIUS_SQ && dSq > 0) {
        const d = Math.sqrt(dSq);
        p.vx += (dx / d) * 0.015;
        p.vy += (dy / d) * 0.015;
      }

      p.x += p.vx;
      p.y += p.vy;
      p.vx *= 0.99;
      p.vy *= 0.99;

      // Maintain minimum drift so particles never stop
      const speed = p.vx * p.vx + p.vy * p.vy;
      if (speed < 0.006) {
        const a = Math.random() * Math.PI * 2;
        p.vx = Math.cos(a) * 0.12;
        p.vy = Math.sin(a) * 0.12;
      }

      // Edge-wrap (smoother than bouncing)
      if (p.x < -20) p.x = canvas.width + 20;
      else if (p.x > canvas.width + 20) p.x = -20;
      if (p.y < -20) p.y = canvas.height + 20;
      else if (p.y > canvas.height + 20) p.y = -20;
    }

    // Inter-particle connections
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dSq = dx * dx + dy * dy;
        if (dSq < MAX_DIST_SQ) {
          const alpha = (1 - Math.sqrt(dSq) / MAX_DIST) * 0.12;
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = `rgba(${COLOR}, ${alpha})`;
          ctx.lineWidth = 0.5;
          ctx.stroke();
        }
      }
    }

    // Draw dots with proximity glow
    for (const p of particles) {
      const dx = mouseX - p.x;
      const dy = mouseY - p.y;
      const dSq = dx * dx + dy * dy;
      const near = dSq < MOUSE_RADIUS_SQ ? 1 - Math.sqrt(dSq) / MOUSE_RADIUS : 0;

      ctx.beginPath();
      ctx.arc(p.x, p.y, 1.5 + near * 2, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${COLOR}, ${0.25 + near * 0.5})`;
      ctx.fill();

      // Halo on close particles
      if (near > 0.3) {
        ctx.beginPath();
        ctx.arc(p.x, p.y, 6 + near * 4, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${COLOR}, ${near * 0.06})`;
        ctx.fill();
      }
    }

    // Cursor-to-particle connections
    if (mouseX > 0) {
      for (const p of particles) {
        const dx = mouseX - p.x;
        const dy = mouseY - p.y;
        const dSq = dx * dx + dy * dy;
        if (dSq < MOUSE_RADIUS_SQ) {
          const d = Math.sqrt(dSq);
          ctx.beginPath();
          ctx.moveTo(mouseX, mouseY);
          ctx.lineTo(p.x, p.y);
          ctx.strokeStyle = `rgba(${COLOR}, ${(1 - d / MOUSE_RADIUS) * 0.15})`;
          ctx.lineWidth = 0.6;
          ctx.stroke();
        }
      }
    }

    frameId = requestAnimationFrame(draw);
  }

  const onMove = (e: MouseEvent) => {
    mouseX = e.clientX;
    mouseY = e.clientY;
  };
  const onLeave = () => {
    mouseX = -1000;
    mouseY = -1000;
  };

  resize();
  seed();
  frameId = requestAnimationFrame(draw);
  window.addEventListener("resize", resize);
  window.addEventListener("mousemove", onMove);
  document.addEventListener("mouseleave", onLeave);

  return () => {
    cancelAnimationFrame(frameId);
    window.removeEventListener("resize", resize);
    window.removeEventListener("mousemove", onMove);
    document.removeEventListener("mouseleave", onLeave);
  };
}

export function ParticleNetwork() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    // Skip on touch devices and small screens
    if ("ontouchstart" in window || window.innerWidth < 768) return;
    // Respect reduced motion preference
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    return startAnimation(canvas, ctx);
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 z-0 pointer-events-none"
      aria-hidden="true"
    />
  );
}
