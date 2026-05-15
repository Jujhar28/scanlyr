import type { ReactNode } from "react";

import { cn } from "@/lib/utils/cn";

type StatCardProps = {
  label: string;
  value: ReactNode;
  hint?: string;
  icon?: ReactNode;
  trend?: ReactNode;
  className?: string;
};

export function StatCard({ label, value, hint, icon, trend, className }: StatCardProps) {
  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-xl border border-[var(--st-border)] bg-[var(--st-surface)] p-5 shadow-sm",
        "before:pointer-events-none before:absolute before:inset-x-0 before:top-0 before:h-px before:bg-gradient-to-r before:from-transparent before:via-cyan-500/35 before:to-transparent",
        className,
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 space-y-2">
          <p className="text-xs font-medium uppercase tracking-wider text-[var(--st-fg-muted)]">{label}</p>
          <p className="text-2xl font-semibold tabular-nums tracking-tight text-[var(--st-fg)] md:text-3xl">
            {value}
          </p>
          {hint ? <p className="text-xs text-[var(--st-fg-muted)]">{hint}</p> : null}
          {trend ? <div className="pt-1">{trend}</div> : null}
        </div>
        {icon ? (
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[var(--st-muted)] text-cyan-400/90">
            {icon}
          </div>
        ) : null}
      </div>
    </div>
  );
}
