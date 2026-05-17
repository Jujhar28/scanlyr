"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { ShieldAlert } from "lucide-react";

import { EventTrendChart, SeverityDonut, ToolBarChart } from "@/components/dashboard/charts";
import { PageHeader } from "@/components/dashboard/page-header";
import { StatCard } from "@/components/dashboard/stat-card";
import { Skeleton } from "@/components/ui/skeleton";
import { fetchAllDetections, type DetectionItem } from "@/lib/api/detections";
import { ApiError } from "@/lib/api/client";
import { useAuth } from "@/providers/auth-provider";

function scoreOf(row: DetectionItem): number | null {
  const r = row.risk_scores.find((s) => s.score_kind === "detection");
  return r ? Number(r.score) : null;
}

export default function RiskAnalyticsPage() {
  const { hydrated } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [items, setItems] = useState<DetectionItem[]>([]);
  const [total, setTotal] = useState(0);
  const [info, setInfo] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    setInfo(null);
    try {
      const res = await fetchAllDetections({ maxItems: 500 });
      setItems(res.items);
      setTotal(res.total);
      if (res.truncated) {
        setInfo(`Charts use the first ${res.items.length} of ${res.total} detection events.`);
      }
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to load analytics.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    void load();
  }, [hydrated, load]);

  const metrics = useMemo(() => {
    let sum = 0;
    let n = 0;
    let high = 0;
    const sev: Record<string, number> = {};
    const tools: Record<string, number> = {};
    const byDay: Record<string, number> = {};
    for (const ev of items) {
      const sc = scoreOf(ev);
      if (sc != null) {
        sum += sc;
        n += 1;
      }
      if (ev.severity === "high" || ev.severity === "critical") high += 1;
      sev[ev.severity] = (sev[ev.severity] ?? 0) + 1;
      const t = (ev.tool_name ?? "Unknown").slice(0, 28);
      tools[t] = (tools[t] ?? 0) + 1;
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
      .slice(0, 8)
      .map(([name, count]) => ({ name, count }));
    const trendKeys = Object.keys(byDay).sort().slice(-21);
    const trend = trendKeys.map((day) => ({ day: day.slice(5), count: byDay[day] ?? 0 }));
    return {
      avg: n ? Math.round((sum / n) * 10) / 10 : null,
      high,
      severityData,
      toolData,
      trend,
    };
  }, [items]);

  if (!hydrated) {
    return null;
  }

  return (
    <div className="mx-auto max-w-[1600px] space-y-8">
      <PageHeader
        title="Risk & analytics"
        description="Distributions and velocity derived from AI detection events — use alongside Microsoft 365 admin signals."
      />

      {error ? (
        <div role="alert" className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-100">
          {error}
        </div>
      ) : null}

      {info && !error ? (
        <div role="status" className="rounded-lg border border-[var(--st-border)] bg-[var(--st-muted)]/60 px-4 py-3 text-sm text-[var(--st-fg-muted)]">
          {info}
        </div>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {loading ? (
          <>
            <Skeleton className="h-[120px] rounded-xl" />
            <Skeleton className="h-[120px] rounded-xl" />
            <Skeleton className="h-[120px] rounded-xl" />
          </>
        ) : (
          <>
            <StatCard
              label="Avg. detection score"
              value={metrics.avg ?? "—"}
              hint={`Across ${items.filter((i) => scoreOf(i) != null).length} scored events (loaded)`}
              icon={<ShieldAlert className="h-5 w-5" aria-hidden />}
            />
            <StatCard
              label="High / critical count"
              value={metrics.high}
              hint="Rule engine severity"
              icon={<ShieldAlert className="h-5 w-5" aria-hidden />}
            />
            <StatCard
              label="Org total (API)"
              value={total}
              hint="Total stored detections for tenant"
              icon={<ShieldAlert className="h-5 w-5" aria-hidden />}
            />
          </>
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-[var(--st-border)] bg-[var(--st-surface)] p-5 shadow-sm">
          <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-[var(--st-fg-muted)]">
            Severity distribution
          </h2>
          {loading ? <Skeleton className="h-[220px] rounded-lg" /> : <SeverityDonut data={metrics.severityData} />}
        </div>
        <div className="rounded-xl border border-[var(--st-border)] bg-[var(--st-surface)] p-5 shadow-sm">
          <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-[var(--st-fg-muted)]">
            Tool concentration
          </h2>
          {loading ? <Skeleton className="h-[240px] rounded-lg" /> : <ToolBarChart data={metrics.toolData} />}
        </div>
      </div>

      <div className="rounded-xl border border-[var(--st-border)] bg-[var(--st-surface)] p-5 shadow-sm">
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-[var(--st-fg-muted)]">
          Activity trend
        </h2>
        {loading ? <Skeleton className="h-[240px] rounded-lg" /> : <EventTrendChart data={metrics.trend} />}
      </div>
    </div>
  );
}
