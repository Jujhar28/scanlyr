import * as React from "react";

import { cn } from "@/lib/utils/cn";

export type TextareaProps = React.TextareaHTMLAttributes<HTMLTextAreaElement>;

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, ...props }, ref) => (
    <textarea
      className={cn(
        "flex min-h-[120px] w-full rounded-lg border border-[var(--st-border)] bg-[var(--st-muted)]/40 px-3 py-2 text-sm text-[var(--st-fg)] shadow-inner placeholder:text-[var(--st-fg-muted)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--st-accent-ring)] disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      ref={ref}
      {...props}
    />
  ),
);
Textarea.displayName = "Textarea";

export { Textarea };
