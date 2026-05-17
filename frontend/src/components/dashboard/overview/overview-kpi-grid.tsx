"use client";

import { AlertTriangle, Clock, ScanSearch, ShieldAlert } from "lucide-react";

import type { ScanHistorySummary } from "@/lib/api/scan-history";

import { OverviewMetricCard } from "./overview-metric-card";

function formatRelative(iso: string | null): { primary: string; hint: string } {
  if (!iso) {
    return { primary: "—", hint: "No scans yet" };
  }
  const date = new Date(iso);
  const now = Date.now();
  const diffMs = now - date.getTime();
  const diffMins = Math.floor(diffMs / 60_000);
  const diffHours = Math.floor(diffMs / 3_600_000);
  const diffDays = Math.floor(diffMs / 86_400_000);

  let relative = date.toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
  if (diffMins < 1) relative = "Just now";
  else if (diffMins < 60) relative = `${diffMins}m ago`;
  else if (diffHours < 48) relative = `${diffHours}h ago`;
  else if (diffDays < 14) relative = `${diffDays}d ago`;

  return {
    primary: relative,
    hint: date.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" }),
  };
}

export function OverviewKpiGrid({
  loading,
  lastScan,
  highRiskCount,
  totalScans,
  detectionsTotal,
}: {
  loading?: boolean;
  lastScan: ScanHistorySummary | null;
  highRiskCount: number;
  totalScans: number;
  detectionsTotal: number;
}) {
  const last = formatRelative(lastScan?.scanned_at ?? null);

  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <OverviewMetricCard
        loading={loading}
        label="Last scan"
        value={last.primary}
        hint={lastScan ? `${last.hint} · ${lastScan.risk_level} risk` : "Run a paste scan to start"}
        icon={<Clock className="h-5 w-5" aria-hidden />}
      />
      <OverviewMetricCard
        loading={loading}
        label="High-risk detections"
        value={highRiskCount}
        hint={
          detectionsTotal > 0
            ? `${highRiskCount} of ${detectionsTotal} recent AI events`
            : "Critical and high severity from M365"
        }
        icon={<ShieldAlert className="h-5 w-5" aria-hidden />}
      />
      <OverviewMetricCard
        loading={loading}
        label="Total scans"
        value={totalScans}
        hint="Paste-to-scan workspace history"
        icon={<ScanSearch className="h-5 w-5" aria-hidden />}
      />
      <OverviewMetricCard
        loading={loading}
        label="AI events"
        value={detectionsTotal}
        hint="Microsoft 365 detection signals"
        icon={<AlertTriangle className="h-5 w-5" aria-hidden />}
      />
    </div>
  );
}
