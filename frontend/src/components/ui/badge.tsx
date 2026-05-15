import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils/cn";

const variants = {
  default: "border-[var(--st-border)] bg-[var(--st-muted)] text-[var(--st-fg-muted)]",
  accent: "border-cyan-500/25 bg-cyan-500/10 text-cyan-200",
  success: "border-emerald-500/25 bg-emerald-500/10 text-emerald-200",
  warning: "border-amber-500/25 bg-amber-500/10 text-amber-200",
  danger: "border-red-500/25 bg-red-500/10 text-red-200",
  outline: "border-[var(--st-border)] bg-transparent text-[var(--st-fg-muted)]",
} as const;

export type BadgeProps = HTMLAttributes<HTMLSpanElement> & {
  variant?: keyof typeof variants;
};

export function Badge({ className, variant = "default", ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium uppercase tracking-wide",
        variants[variant],
        className,
      )}
      {...props}
    />
  );
}
