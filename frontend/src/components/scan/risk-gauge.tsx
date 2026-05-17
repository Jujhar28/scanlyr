"use client";

import { cn } from "@/lib/utils/cn";

type RiskLevel = "low" | "medium" | "high" | "critical";

const levelColor: Record<RiskLevel, string> = {
  low: "text-emerald-400",
  medium: "text-amber-400",
  high: "text-rose-400",
  critical: "text-rose-500",
};

const ringColor: Record<RiskLevel, string> = {
  low: "stroke-emerald-400/80",
  medium: "stroke-amber-400/80",
  high: "stroke-rose-400/80",
  critical: "stroke-rose-500/90",
};

const glowColor: Record<RiskLevel, string> = {
  low: "shadow-[0_0_40px_rgba(52,211,153,0.25)]",
  medium: "shadow-[0_0_40px_rgba(251,191,36,0.25)]",
  high: "shadow-[0_0_40px_rgba(244,63,94,0.3)]",
  critical: "shadow-[0_0_48px_rgba(244,63,94,0.45)]",
};

export function RiskGauge({
  score,
  level,
  confidence,
  className,
}: {
  score: number;
  level: RiskLevel;
  confidence: number;
  className?: string;
}) {
  const circumference = 2 * Math.PI * 54;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className={cn("relative flex flex-col items-center", className)}>
      <div className={cn("relative rounded-full", glowColor[level])}>
        <svg width="140" height="140" className="-rotate-90" aria-hidden>
          <circle cx="70" cy="70" r="54" fill="none" stroke="var(--st-muted)" strokeWidth="10" />
          <circle
            cx="70"
            cy="70"
            r="54"
            fill="none"
            className={ringColor[level]}
            strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            style={{ transition: "stroke-dashoffset 0.8s ease-out" }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={cn("font-display text-4xl font-bold tabular-nums", levelColor[level])}>
            {score}
          </span>
          <span className="text-[10px] uppercase tracking-[0.2em] text-[var(--st-fg-muted)]">
            risk score
          </span>
        </div>
        </div>
      <div className="mt-4 flex flex-wrap items-center justify-center gap-2">
        <span
          className={cn(
            "rounded-full border px-3 py-0.5 text-xs font-semibold uppercase tracking-wider",
            level === "low" && "border-emerald-500/30 bg-emerald-500/10 text-emerald-300",
            level === "medium" && "border-amber-500/30 bg-amber-500/10 text-amber-300",
            level === "high" && "border-rose-500/30 bg-rose-500/10 text-rose-300",
            level === "critical" && "border-rose-600/40 bg-rose-600/15 text-rose-200",
          )}
        >
          {level}
        </span>
        <span className="text-xs text-[var(--st-fg-muted)]">
          {(confidence * 100).toFixed(0)}% confidence
        </span>
      </div>
    </div>
  );
}
