"use client";

import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { ButtonLink } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import type { DetectionItem } from "@/lib/api/detections";
import { cn } from "@/lib/utils/cn";

function primaryScore(row: DetectionItem): string {
  const r = row.risk_scores.find((s) => s.score_kind === "detection");
  return r?.score ?? "—";
}

export function AiEventsTable({
  rows,
  loading,
  className,
}: {
  rows: DetectionItem[];
  loading?: boolean;
  className?: string;
}) {
  if (loading) {
    return (
      <div className={cn("space-y-2", className)}>
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-12 w-full rounded-lg" />
        ))}
      </div>
    );
  }

  if (!rows.length) {
    return (
      <div
        className={cn(
          "rounded-xl border border-dashed border-[var(--st-border)] p-10 text-center",
          className,
        )}
      >
        <p className="text-sm text-[var(--st-fg-muted)]">
          No Microsoft AI events yet. Connect Microsoft 365 and run detection to populate this list.
        </p>
        <div className="mt-4 flex flex-wrap justify-center gap-2">
          <ButtonLink href="/dashboard/integrations" variant="secondary" className="h-9 px-4 text-sm">
            Integrations
          </ButtonLink>
          <ButtonLink href="/dashboard/detections" className="h-9 px-4 text-sm">
            AI events
          </ButtonLink>
        </div>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "overflow-hidden rounded-xl border border-[var(--st-border)] bg-[var(--st-surface)] shadow-sm",
        className,
      )}
    >
      <div className="overflow-x-auto">
        <table className="w-full min-w-[720px] text-left text-sm">
          <thead className="border-b border-[var(--st-border)] bg-[var(--st-muted)]/40 text-xs uppercase tracking-wider text-[var(--st-fg-muted)]">
            <tr>
              <th className="px-5 py-3 font-medium">Time</th>
              <th className="px-5 py-3 font-medium">Tool</th>
              <th className="px-5 py-3 font-medium">Severity</th>
              <th className="px-5 py-3 font-medium">Score</th>
              <th className="px-5 py-3 font-medium" />
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--st-border)]">
            {rows.map((row) => (
              <tr key={row.id} className="transition hover:bg-[var(--st-muted)]/30">
                <td className="whitespace-nowrap px-5 py-3 text-[var(--st-fg-muted)]">
                  {new Date(row.occurred_at).toLocaleString()}
                </td>
                <td className="px-5 py-3 font-medium text-[var(--st-fg)]">{row.tool_name ?? "—"}</td>
                <td className="px-5 py-3">
                  <Badge
                    variant={
                      row.severity === "critical" || row.severity === "high"
                        ? "danger"
                        : row.severity === "medium"
                          ? "warning"
                          : "outline"
                    }
                  >
                    {row.severity}
                  </Badge>
                </td>
                <td className="px-5 py-3 tabular-nums text-[var(--st-fg-muted)]">{primaryScore(row)}</td>
                <td className="px-5 py-3 text-right">
                  <Link
                    href={`/dashboard/detections/${row.id}`}
                    className="text-xs font-medium text-[var(--st-accent)] hover:underline"
                  >
                    Details
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
