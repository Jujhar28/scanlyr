"use client";

import { Badge } from "@/components/ui/badge";
import { ButtonLink } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import type { ScanHistorySummary } from "@/lib/api/scan-history";
import { cn } from "@/lib/utils/cn";

function riskBadge(level: ScanHistorySummary["risk_level"]) {
  const variant =
    level === "critical" || level === "high"
      ? "danger"
      : level === "medium"
        ? "warning"
        : "outline";
  return <Badge variant={variant}>{level}</Badge>;
}

function contentTypeLabel(type: ScanHistorySummary["content_type"]) {
  if (type === "prompt") return "Prompt";
  if (type === "output") return "Output";
  return "Auto";
}

export function ScanHistoryTable({
  rows,
  loading,
  className,
}: {
  rows: ScanHistorySummary[];
  loading?: boolean;
  className?: string;
}) {
  if (loading) {
    return (
      <div className={cn("space-y-2", className)}>
        {Array.from({ length: 6 }).map((_, i) => (
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
          No paste scans yet. Run a security scan to analyze prompts or model output.
        </p>
        <ButtonLink href="/dashboard/scan" className="mt-4 h-9 px-4 text-sm">
          New security scan
        </ButtonLink>
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
        <table className="w-full min-w-[800px] text-left text-sm">
          <thead className="border-b border-[var(--st-border)] bg-[var(--st-muted)]/40 text-xs uppercase tracking-wider text-[var(--st-fg-muted)]">
            <tr>
              <th className="px-5 py-3 font-medium">Time</th>
              <th className="px-5 py-3 font-medium">Type</th>
              <th className="px-5 py-3 font-medium">Preview</th>
              <th className="px-5 py-3 font-medium">Risk</th>
              <th className="px-5 py-3 font-medium">Score</th>
              <th className="px-5 py-3 font-medium">Findings</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--st-border)]">
            {rows.map((row) => (
              <tr key={row.id} className="transition hover:bg-[var(--st-muted)]/30">
                <td className="whitespace-nowrap px-5 py-3 text-[var(--st-fg-muted)]">
                  {new Date(row.scanned_at).toLocaleString()}
                </td>
                <td className="px-5 py-3 text-[var(--st-fg)]">{contentTypeLabel(row.content_type)}</td>
                <td className="max-w-[320px] truncate px-5 py-3 font-mono text-xs text-[var(--st-fg-muted)]">
                  {row.input_preview || "—"}
                </td>
                <td className="px-5 py-3">{riskBadge(row.risk_level)}</td>
                <td className="px-5 py-3 tabular-nums font-semibold text-[var(--st-fg)]">{row.risk_score}</td>
                <td className="px-5 py-3 tabular-nums text-[var(--st-fg-muted)]">{row.finding_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
