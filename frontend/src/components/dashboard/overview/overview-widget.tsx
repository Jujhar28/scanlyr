"use client";

import Link from "next/link";
import type { ReactNode } from "react";

import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils/cn";

export function OverviewWidget({
  title,
  description,
  action,
  actionHref,
  loading,
  empty,
  children,
  className,
}: {
  title: string;
  description?: string;
  action?: string;
  actionHref?: string;
  loading?: boolean;
  empty?: ReactNode;
  children?: ReactNode;
  className?: string;
}) {
  const showEmpty = !loading && empty != null && !children;

  return (
    <section
      className={cn(
        "flex h-full flex-col overflow-hidden rounded-xl border border-[var(--st-border)] bg-[var(--st-surface)] shadow-sm",
        "before:pointer-events-none before:block before:h-px before:bg-gradient-to-r before:from-transparent before:via-cyan-500/25 before:to-transparent",
        className,
      )}
    >
      <header className="flex flex-wrap items-start justify-between gap-2 border-b border-[var(--st-border)]/80 px-5 py-4">
        <div className="min-w-0">
          <h2 className="text-sm font-semibold tracking-tight text-[var(--st-fg)]">{title}</h2>
          {description ? (
            <p className="mt-0.5 text-xs text-[var(--st-fg-muted)]">{description}</p>
          ) : null}
        </div>
        {action && actionHref ? (
          <Link
            href={actionHref}
            className="shrink-0 text-xs font-medium text-[var(--st-accent)] hover:underline"
          >
            {action}
          </Link>
        ) : null}
      </header>

      <div className="flex flex-1 flex-col p-5">
        {loading ? (
          <div className="space-y-3">
            <Skeleton className="h-8 w-2/3 rounded-md" />
            <Skeleton className="h-4 w-full rounded-md" />
            <Skeleton className="h-4 w-4/5 rounded-md" />
          </div>
        ) : showEmpty ? (
          empty
        ) : (
          children
        )}
      </div>
    </section>
  );
}

export function OverviewEmptyState({
  message,
  action,
  actionHref,
}: {
  message: string;
  action?: string;
  actionHref?: string;
}) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center rounded-lg border border-dashed border-[var(--st-border)] bg-[var(--st-muted)]/20 px-4 py-8 text-center">
      <p className="text-sm text-[var(--st-fg-muted)]">{message}</p>
      {action && actionHref ? (
        <Link
          href={actionHref}
          className="mt-3 text-sm font-medium text-[var(--st-accent)] hover:underline"
        >
          {action}
        </Link>
      ) : null}
    </div>
  );
}
