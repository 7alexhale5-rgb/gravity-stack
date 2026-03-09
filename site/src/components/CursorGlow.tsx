"use client";

import { useEffect, useState } from "react";

export function CursorGlow() {
  const [position, setPosition] = useState({ x: -100, y: -100 });
  const [isTouch, setIsTouch] = useState(false);

  useEffect(() => {
    // Detect touch device
    const checkTouch = () => setIsTouch(true);
    window.addEventListener("touchstart", checkTouch, { once: true });

    const handleMouseMove = (e: MouseEvent) => {
      setPosition({ x: e.clientX, y: e.clientY });
    };

    window.addEventListener("mousemove", handleMouseMove);
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("touchstart", checkTouch);
    };
  }, []);

  if (isTouch) return null;

  return (
    <div
      className="fixed pointer-events-none z-[9998] transition-opacity duration-300"
      style={{
        left: position.x - 200,
        top: position.y - 200,
        width: 400,
        height: 400,
        background: "radial-gradient(circle, rgba(0,212,255,0.04) 0%, transparent 70%)",
        willChange: "left, top",
      }}
      aria-hidden="true"
    />
  );
}
