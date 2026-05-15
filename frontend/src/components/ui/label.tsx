import type { LabelHTMLAttributes } from "react";

import { cn } from "@/lib/utils/cn";

export type LabelProps = LabelHTMLAttributes<HTMLLabelElement>;

export function Label({ className, ...props }: LabelProps) {
  return (
    <label
      className={cn("text-sm font-medium text-[var(--st-fg)]", className)}
      {...props}
    />
  );
}
