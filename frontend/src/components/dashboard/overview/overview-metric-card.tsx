"use client";

import type { ReactNode } from "react";

import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils/cn";

export function OverviewMetricCard({
  label,
  value,
  hint,
  icon,
  loading,
  className,
}: {
  label: string;
  value: ReactNode;
  hint?: string;
  icon?: ReactNode;
  loading?: boolean;
  className?: string;
}) {
  if (loading) {
    return <Skeleton className={cn("h-[118px] w-full rounded-xl", className)} />;
  }

  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-xl border border-[var(--st-border)] bg-[var(--st-surface)] p-5 shadow-sm",
        "before:pointer-events-none before:absolute before:inset-x-0 before:top-0 before:h-px before:bg-gradient-to-r before:from-transparent before:via-cyan-500/30 before:to-transparent",
        className,
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 space-y-1.5">
          <p className="text-xs font-medium uppercase tracking-wider text-[var(--st-fg-muted)]">{label}</p>
          <p className="text-2xl font-semibold tabular-nums tracking-tight text-[var(--st-fg)] sm:text-3xl">
            {value}
          </p>
          {hint ? <p className="text-xs leading-relaxed text-[var(--st-fg-muted)]">{hint}</p> : null}
        </div>
        {icon ? (
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[var(--st-muted)] text-[var(--st-accent)]">
            {icon}
          </div>
        ) : null}
      </div>
    </div>
  );
}
