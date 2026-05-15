"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Activity, FileText, Plug, Server } from "lucide-react";

import { EventTrendChart, SeverityDonut, ToolBarChart } from "@/components/dashboard/charts";
import { PageHeader } from "@/components/dashboard/page-header";
import { StatCard } from "@/components/dashboard/stat-card";
import { Badge } from "@/components/ui/badge";
import { ButtonLink } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { apiFetch, ApiError } from "@/lib/api/client";
import { useAuth } from "@/providers/auth-provider";

type DetectionItem = {
  id: string;
  occurred_at: string;
  tool_name: string | null;
  severity: string;
  risk_scores: { score_kind: string; score: string }[];
};

type DetectionsList = { items: DetectionItem[]; total: number };
type ReportsList = { total: number };
type Health = { status: string };
type MsftStatus = { status: string; last_sync_at: string | null };

function detectionScore(row: DetectionItem): number | null {
  const r = row.risk_scores.find((s) => s.score_kind === "detection");
  return r ? Number(r.score) : null;
}

export function OverviewDashboard() {
  const { hydrated } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [detections, setDetections] = useState<DetectionsList | null>(null);
  const [reports, setReports] = useState<ReportsList | null>(null);
  const [health, setHealth] = useState<Health | null>(null);
  const [msft, setMsft] = useState<MsftStatus | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [d, r, h, m] = await Promise.all([
        apiFetch<DetectionsList>("detections?limit=200&offset=0"),
        apiFetch<ReportsList>("reports?limit=1&offset=0"),
        apiFetch<Health>("health", { auth: false }).catch(() => ({ status: "unreachable" })),
        apiFetch<MsftStatus>("integrations/microsoft/status").catch(() => ({ status: "unknown", last_sync_at: null })),
      ]);
      setDetections(d);
      setReports(r);
      setHealth(h);
      setMsft(m);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to load dashboard.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    void load();
  }, [hydrated, load]);

  const charts = useMemo(() => {
    const items = detections?.items ?? [];
    const sev: Record<string, number> = {};
    const tools: Record<string, number> = {};
    const byDay: Record<string, number> = {};
    let high = 0;
    for (const ev of items) {
      sev[ev.severity] = (sev[ev.severity] ?? 0) + 1;
      const t = (ev.tool_name ?? "Unknown").slice(0, 24);
      tools[t] = (tools[t] ?? 0) + 1;
      if (ev.severity === "high" || ev.severity === "critical") high += 1;
      const d = new Date(ev.occurred_at);
      const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
      byDay[key] = (byDay[key] ?? 0) + 1;
    }
    const severityData = ["critical", "high", "medium", "low", "info"].map((name) => ({
      name,
      value: sev[name] ?? 0,
    }));
    const toolData = Object.entries(tools)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 6)
      .map(([name, count]) => ({ name, count }));
    const trendKeys = Object.keys(byDay).sort().slice(-14);
    const trend = trendKeys.map((day) => ({ day: day.slice(5), count: byDay[day] ?? 0 }));
    return { severityData, toolData, trend, high };
  }, [detections]);

  if (!hydrated) {
    return null;
  }

  return (
    <div className="mx-auto max-w-[1600px] space-y-8">
      <PageHeader
        title="Overview"
        description="Posture across AI detections, integrations, and reporting — unified for security and GRC teams."
        actions={
          <ButtonLink href="/dashboard/detections" variant="secondary" className="h-9 px-3 text-sm">
            View AI events
          </ButtonLink>
        }
      />

      {error ? (
        <div
          role="alert"
          className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-100"
        >
          {error}
        </div>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {loading ? (
          <>
            {[1, 2, 3, 4].map((i) => (
              <Skeleton key={i} className="h-[120px] w-full rounded-xl" />
            ))}
          </>
        ) : (
          <>
            <StatCard
              label="AI events (window)"
              value={detections?.total ?? 0}
              hint="Last 200 loaded for analytics"
              icon={<Activity className="h-5 w-5" aria-hidden />}
            />
            <StatCard
              label="High / critical"
              value={charts.high}
              hint="Severity from rule engine"
              icon={<Activity className="h-5 w-5" aria-hidden />}
            />
            <StatCard
              label="Reports generated"
              value={reports?.total ?? 0}
              hint="Compliance PDF history"
              icon={<FileText className="h-5 w-5" aria-hidden />}
            />
            <StatCard
              label="API"
              value={health?.status === "ok" ? "Operational" : "Check"}
              hint="Control plane reachability"
              icon={<Server className="h-5 w-5" aria-hidden />}
              trend={
                msft ? (
                  <Badge variant={msft.status === "connected" ? "success" : "outline"} className="normal-case">
                    M365 {msft.status}
                  </Badge>
                ) : null
              }
            />
          </>
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="rounded-xl border border-[var(--st-border)] bg-[var(--st-surface)] p-5 shadow-sm lg:col-span-1">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-[var(--st-fg-muted)]">
              Severity mix
            </h2>
          </div>
          {loading ? <Skeleton className="h-[220px] w-full rounded-lg" /> : <SeverityDonut data={charts.severityData} />}
        </div>
        <div className="rounded-xl border border-[var(--st-border)] bg-[var(--st-surface)] p-5 shadow-sm lg:col-span-2">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-[var(--st-fg-muted)]">
              Top tools observed
            </h2>
          </div>
          {loading ? <Skeleton className="h-[240px] w-full rounded-lg" /> : <ToolBarChart data={charts.toolData} />}
        </div>
      </div>

      <div className="rounded-xl border border-[var(--st-border)] bg-[var(--st-surface)] p-5 shadow-sm">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-[var(--st-fg-muted)]">
            Event volume (by day)
          </h2>
          <Link href="/dashboard/risk" className="text-xs font-medium text-[var(--st-accent)] hover:underline">
            Open risk analytics →
          </Link>
        </div>
        {loading ? <Skeleton className="h-[240px] w-full rounded-lg" /> : <EventTrendChart data={charts.trend} />}
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Link
          href="/dashboard/integrations"
          className="group rounded-xl border border-[var(--st-border)] bg-[var(--st-surface)] p-5 transition hover:border-cyan-500/30 hover:shadow-md"
        >
          <div className="flex items-center gap-3">
            <Plug className="h-8 w-8 text-cyan-400/80" />
            <div>
              <p className="text-sm font-semibold text-[var(--st-fg)]">Integrations</p>
              <p className="text-xs text-[var(--st-fg-muted)]">Microsoft 365 & ingestion</p>
            </div>
          </div>
        </Link>
        <Link
          href="/dashboard/reports"
          className="group rounded-xl border border-[var(--st-border)] bg-[var(--st-surface)] p-5 transition hover:border-cyan-500/30 hover:shadow-md"
        >
          <div className="flex items-center gap-3">
            <FileText className="h-8 w-8 text-cyan-400/80" />
            <div>
              <p className="text-sm font-semibold text-[var(--st-fg)]">Reports</p>
              <p className="text-xs text-[var(--st-fg-muted)]">PDF governance packs</p>
            </div>
          </div>
        </Link>
        <Link
          href="/dashboard/settings"
          className="group rounded-xl border border-[var(--st-border)] bg-[var(--st-surface)] p-5 transition hover:border-cyan-500/30 hover:shadow-md"
        >
          <div className="flex items-center gap-3">
            <Server className="h-8 w-8 text-cyan-400/80" />
            <div>
              <p className="text-sm font-semibold text-[var(--st-fg)]">Organization</p>
              <p className="text-xs text-[var(--st-fg-muted)]">Tenant & access</p>
            </div>
          </div>
        </Link>
      </div>

      {!loading && detections && detections.items.length > 0 ? (
        <div className="rounded-xl border border-[var(--st-border)] bg-[var(--st-surface)] shadow-sm">
          <div className="flex items-center justify-between border-b border-[var(--st-border)] px-5 py-4">
            <h2 className="text-sm font-semibold text-[var(--st-fg)]">Recent AI events</h2>
            <Link href="/dashboard/detections" className="text-xs font-medium text-[var(--st-accent)] hover:underline">
              View all
            </Link>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-left text-sm">
              <thead className="border-b border-[var(--st-border)] bg-[var(--st-muted)]/50 text-xs uppercase tracking-wider text-[var(--st-fg-muted)]">
                <tr>
                  <th className="px-5 py-3 font-medium">Time</th>
                  <th className="px-5 py-3 font-medium">Tool</th>
                  <th className="px-5 py-3 font-medium">Severity</th>
                  <th className="px-5 py-3 font-medium">Score</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--st-border)]">
                {detections.items.slice(0, 8).map((row) => (
                  <tr key={row.id} className="hover:bg-[var(--st-muted)]/40">
                    <td className="whitespace-nowrap px-5 py-3 text-[var(--st-fg-muted)]">
                      {new Date(row.occurred_at).toLocaleString()}
                    </td>
                    <td className="px-5 py-3 font-medium text-[var(--st-fg)]">{row.tool_name ?? "—"}</td>
                    <td className="px-5 py-3">
                      <Badge variant={row.severity === "critical" || row.severity === "high" ? "danger" : "outline"}>
                        {row.severity}
                      </Badge>
                    </td>
                    <td className="px-5 py-3 tabular-nums text-[var(--st-fg-muted)]">
                      {detectionScore(row) ?? "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}
    </div>
  );
}
