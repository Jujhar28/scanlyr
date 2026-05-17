"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import type { ReactNode } from "react";
import { ArrowUpRight } from "lucide-react";

import { cn } from "@/lib/utils/cn";

type IntelCardProps = {
  title?: string;
  description?: string;
  action?: string;
  actionHref?: string;
  children: ReactNode;
  className?: string;
  span?: "default" | "wide" | "tall";
  accent?: "cyan" | "indigo" | "neon" | "amber" | "none";
  noPadding?: boolean;
};

const accentBorder = {
  cyan: "hover:border-[var(--st-accent)]/40 hover:shadow-[var(--st-card-hover)]",
  indigo: "hover:border-indigo-300/50 hover:shadow-[0_16px_48px_rgba(67,56,202,0.12)]",
  neon: "hover:border-emerald-400/40 hover:shadow-[0_16px_48px_rgba(22,212,107,0.12)]",
  amber: "hover:border-amber-400/40 hover:shadow-[0_16px_48px_rgba(245,158,11,0.12)]",
  none: "hover:shadow-[var(--st-shadow-lg)]",
};

export function IntelCard({
  title,
  description,
  action,
  actionHref,
  children,
  className,
  span = "default",
  accent = "cyan",
  noPadding,
}: IntelCardProps) {
  return (
    <motion.article
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
      whileHover={{ y: -3 }}
      className={cn(
        "group relative overflow-hidden rounded-2xl border border-[var(--st-border)] bg-[var(--st-surface)] shadow-[var(--st-shadow)] transition-[border-color,box-shadow] duration-300",
        accentBorder[accent],
        span === "wide" && "lg:col-span-2",
        span === "tall" && "lg:row-span-2",
        className,
      )}
    >
      <motion.div
        className="pointer-events-none absolute -right-12 -top-12 h-32 w-32 rounded-full bg-[var(--st-accent)]/5 blur-2xl"
        animate={{ scale: [1, 1.15, 1], opacity: [0.3, 0.5, 0.3] }}
        transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
      />
      {(title || description || action) && (
        <header className="flex items-start justify-between gap-3 border-b border-[var(--st-border)] px-5 py-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
          >
            {title ? (
              <h2 className="font-display text-sm font-semibold tracking-tight text-[var(--st-fg)]">
                {title}
              </h2>
            ) : null}
            {description ? (
              <p className="mt-0.5 text-xs text-[var(--st-fg-muted)]">{description}</p>
            ) : null}
          </motion.div>
          {action && actionHref ? (
            <Link
              href={actionHref}
              className="inline-flex shrink-0 items-center gap-0.5 text-xs font-semibold text-[var(--st-accent)] transition hover:text-[var(--st-accent-hover)]"
            >
              {action}
              <ArrowUpRight className="h-3.5 w-3.5" aria-hidden />
            </Link>
          ) : null}
        </header>
      )}
      <motion.div className={cn(!noPadding && "p-5")}>{children}</motion.div>
    </motion.article>
  );
}
