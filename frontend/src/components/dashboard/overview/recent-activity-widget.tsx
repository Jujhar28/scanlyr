"use client";

import Link from "next/link";
import { FileSearch, Radar } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import type { OverviewActivityItem } from "@/lib/overview/types";
import { cn } from "@/lib/utils/cn";

import { OverviewEmptyState, OverviewWidget } from "./overview-widget";

function severityVariant(severity?: string): "danger" | "warning" | "outline" {
  if (severity === "critical" || severity === "high") return "danger";
  if (severity === "medium") return "warning";
  return "outline";
}

function ActivityIcon({ kind }: { kind: OverviewActivityItem["kind"] }) {
  if (kind === "paste_scan") {
    return <FileSearch className="h-4 w-4 text-[var(--st-accent)]" aria-hidden />;
  }
  return <Radar className="h-4 w-4 text-cyan-400" aria-hidden />;
}

export function RecentActivityWidget({
  items,
  loading,
}: {
  items: OverviewActivityItem[];
  loading?: boolean;
}) {
  return (
    <OverviewWidget
      title="Recent activity"
      description="Latest paste scans and Microsoft AI events"
      action="View history"
      actionHref="/dashboard/history"
      loading={loading}
      empty={
        <OverviewEmptyState
          message="No activity yet. Connect Microsoft 365 or run a security scan to see events here."
          action="Get started"
          actionHref="/dashboard/integrations"
        />
      }
    >
      {items.length > 0 ? (
        <ul className="divide-y divide-[var(--st-border)]">
          {items.map((item) => (
            <li key={item.id}>
              <Link
                href={item.href}
                className="group flex gap-3 py-3 transition first:pt-0 last:pb-0 hover:opacity-90"
              >
                <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[var(--st-muted)]/80">
                  <ActivityIcon kind={item.kind} />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="truncate text-sm font-medium text-[var(--st-fg)] group-hover:text-[var(--st-accent)]">
                      {item.title}
                    </p>
                    {item.severity ? (
                      <Badge variant={severityVariant(item.severity)} className="normal-case">
                        {item.severity}
                      </Badge>
                    ) : null}
                  </div>
                  <p className="mt-0.5 truncate text-xs text-[var(--st-fg-muted)]">{item.subtitle}</p>
                  <p className="mt-1 text-xs tabular-nums text-[var(--st-fg-muted)]">
                    {new Date(item.occurredAt).toLocaleString(undefined, {
                      month: "short",
                      day: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                    {item.riskScore != null ? (
                      <span className={cn("ml-2 font-medium", item.riskScore >= 70 && "text-rose-400")}>
                        · Score {item.riskScore}
                      </span>
                    ) : null}
                  </p>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      ) : null}
    </OverviewWidget>
  );
}
