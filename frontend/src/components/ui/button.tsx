import type { AnchorHTMLAttributes, ButtonHTMLAttributes, ReactNode } from "react";
import Link from "next/link";
import type { LinkProps } from "next/link";

import { cn } from "@/lib/utils/cn";

const baseClass =
  "inline-flex h-10 items-center justify-center gap-2 rounded-lg px-4 text-sm font-medium transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--st-accent)]";

const variants = {
  primary:
    "bg-[var(--st-accent)] text-white hover:opacity-90 disabled:opacity-50 shadow-sm",
  secondary:
    "border border-[var(--st-border)] bg-[var(--st-surface)] text-[var(--st-fg)] hover:bg-[var(--st-muted)] disabled:opacity-50",
  ghost:
    "text-[var(--st-fg-muted)] hover:bg-[var(--st-muted)] disabled:opacity-50",
} as const;

export type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: keyof typeof variants;
};

export function Button({
  className,
  variant = "primary",
  type = "button",
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      className={cn(baseClass, variants[variant], className)}
      {...props}
    />
  );
}

export type ButtonLinkProps = LinkProps &
  Omit<AnchorHTMLAttributes<HTMLAnchorElement>, keyof LinkProps> & {
    variant?: keyof typeof variants;
    className?: string;
    children: ReactNode;
  };

export function ButtonLink({
  className,
  variant = "primary",
  ...props
}: ButtonLinkProps) {
  return (
    <Link className={cn(baseClass, variants[variant], className)} {...props} />
  );
}
