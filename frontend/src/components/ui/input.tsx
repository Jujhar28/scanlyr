import type { InputHTMLAttributes } from "react";

import { cn } from "@/lib/utils/cn";

export type InputProps = InputHTMLAttributes<HTMLInputElement>;

export function Input({ className, ...props }: InputProps) {
  return (
    <input
      className={cn(
        "h-10 w-full rounded-lg border border-[var(--st-border)] bg-[var(--st-surface)] px-3 text-sm text-[var(--st-fg)] shadow-inner outline-none transition placeholder:text-[var(--st-fg-muted)] focus:border-[var(--st-accent)] focus:ring-2 focus:ring-[var(--st-accent-ring)] disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      {...props}
    />
  );
}
