"use client";

import { motion, useMotionValueEvent, useSpring, useTransform } from "framer-motion";
import { useEffect, useState } from "react";

import { cn } from "@/lib/utils/cn";

type RiskLevel = "low" | "medium" | "high" | "critical";

const levelStyles: Record<
  RiskLevel,
  { text: string; ring: string; glow: string; badge: string }
> = {
  low: {
    text: "text-emerald-600",
    ring: "stroke-emerald-500",
    glow: "shadow-[0_0_32px_rgba(22,212,107,0.35)]",
    badge: "border-emerald-500/30 bg-emerald-50 text-emerald-700",
  },
  medium: {
    text: "text-amber-600",
    ring: "stroke-amber-500",
    glow: "shadow-[0_0_32px_rgba(245,158,11,0.35)]",
    badge: "border-amber-500/30 bg-amber-50 text-amber-800",
  },
  high: {
    text: "text-rose-600",
    ring: "stroke-rose-500",
    glow: "shadow-[0_0_36px_rgba(225,29,72,0.35)]",
    badge: "border-rose-500/30 bg-rose-50 text-rose-700",
  },
  critical: {
    text: "text-rose-700",
    ring: "stroke-rose-600",
    glow: "shadow-[0_0_40px_rgba(190,18,60,0.45)]",
    badge: "border-rose-600/40 bg-rose-100 text-rose-800",
  },
};

export function AnimatedRiskGauge({
  score,
  level,
  confidence,
  animateKey,
  size = "lg",
  className,
}: {
  score: number;
  level: RiskLevel;
  confidence?: number;
  /** Change to re-trigger count-up animation */
  animateKey?: string | number;
  size?: "md" | "lg";
  className?: string;
}) {
  const styles = levelStyles[level];
  const spring = useSpring(0, { stiffness: 60, damping: 18 });
  const [displayScore, setDisplayScore] = useState(0);
  const circumference = 2 * Math.PI * (size === "lg" ? 54 : 42);
  const dashOffset = useTransform(spring, (v) => circumference - (v / 100) * circumference);

  useMotionValueEvent(spring, "change", (v) => setDisplayScore(Math.round(v)));

  const dim = size === "lg" ? 140 : 108;
  const r = size === "lg" ? 54 : 42;

  useEffect(() => {
    spring.set(0);
    const t = requestAnimationFrame(() => spring.set(score));
    return () => cancelAnimationFrame(t);
  }, [score, animateKey, spring]);

  return (
    <div className={cn("relative flex flex-col items-center", className)}>
      <div className={cn("relative rounded-full", styles.glow)}>
        <svg width={dim} height={dim} className="-rotate-90" aria-hidden>
          <circle
            cx={dim / 2}
            cy={dim / 2}
            r={r}
            fill="none"
            stroke="var(--st-muted)"
            strokeWidth={size === "lg" ? 10 : 8}
          />
          <motion.circle
            cx={dim / 2}
            cy={dim / 2}
            r={r}
            fill="none"
            className={styles.ring}
            strokeWidth={size === "lg" ? 10 : 8}
            strokeLinecap="round"
            strokeDasharray={circumference}
            style={{ strokeDashoffset: dashOffset }}
          />
        </svg>
        <motion.div
          className="absolute inset-0 flex flex-col items-center justify-center"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2, duration: 0.4 }}
        >
          <span
            className={cn(
              "font-display font-bold tabular-nums",
              size === "lg" ? "text-4xl" : "text-3xl",
              styles.text,
            )}
          >
            {displayScore}
          </span>
          <span className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--st-fg-muted)]">
            risk score
          </span>
        </motion.div>
      </div>
      <div className="mt-4 flex flex-wrap items-center justify-center gap-2">
        <span
          className={cn(
            "rounded-full border px-3 py-0.5 text-xs font-semibold uppercase tracking-wider",
            styles.badge,
          )}
        >
          {level}
        </span>
        {confidence != null ? (
          <span className="text-xs text-[var(--st-fg-muted)]">
            {(confidence * 100).toFixed(0)}% confidence
          </span>
        ) : null}
      </div>
    </div>
  );
}
