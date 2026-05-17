"use client";

import type { CategoryScore } from "@/lib/api/scan";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils/cn";

export function CategoryBreakdown({ categories }: { categories: CategoryScore[] }) {
  if (!categories.length) {
    return (
      <p className="text-sm text-[var(--st-fg-muted)]">No category-level risk signals detected.</p>
    );
  }

  return (
    <ul className="space-y-4">
      {categories.map((cat) => (
        <li key={cat.risk_category}>
          <div className="mb-1.5 flex items-center justify-between gap-2 text-sm">
            <span className="font-medium capitalize text-[var(--st-fg)]">
              {cat.risk_category.replace(/_/g, " ")}
            </span>
            <span className="font-mono tabular-nums text-[var(--st-fg-muted)]">{cat.score}</span>
          </div>
          <Progress
            value={cat.score}
            indicatorClassName={cn(
              cat.score >= 80 && "bg-rose-400",
              cat.score >= 40 && cat.score < 80 && "bg-amber-400",
              cat.score < 40 && "bg-emerald-400",
            )}
          />
          <p className="mt-1.5 text-xs leading-relaxed text-[var(--st-fg-muted)]">{cat.explanation}</p>
        </li>
      ))}
    </ul>
  );
}
