import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils/cn";

const variants = {
  accent: "border-cyan-500/25 bg-cyan-50 text-cyan-800",
  success: "border-emerald-500/25 bg-emerald-50 text-emerald-800",
  warning: "border-amber-500/25 bg-amber-50 text-amber-900",
  danger: "border-rose-500/25 bg-rose-50 text-rose-800",
  outline: "border-[var(--st-border-strong)] bg-[var(--st-muted)] text-[var(--st-fg-muted)]",
} as const;

export function Badge({
  className,
  variant = "outline",
  ...props
}: HTMLAttributes<HTMLSpanElement> & { variant?: keyof typeof variants }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide",
        variants[variant],
        className,
      )}
      {...props}
    />
  );
}
