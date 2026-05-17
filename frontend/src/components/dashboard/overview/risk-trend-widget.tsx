"use client";

import { useMemo } from "react";
import {
  Bar,
  CartesianGrid,
  Line,
  ComposedChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { ScanAnalyticsResponse } from "@/lib/api/scan-analytics";
import { Badge } from "@/components/ui/badge";

import { OverviewEmptyState, OverviewWidget } from "./overview-widget";

const GRID = "rgba(148, 163, 184, 0.08)";
const AXIS = "#64748b";

function formatTrendLabel(iso: string): string {
  const d = new Date(iso);
  return `${d.getMonth() + 1}/${d.getDate()}`;
}

export function RiskTrendWidget({
  analytics,
  loading,
}: {
  analytics: ScanAnalyticsResponse | null;
  loading?: boolean;
}) {
  const chartData = useMemo(() => {
    if (!analytics?.trends.length) return [];
    return analytics.trends.map((t) => ({
      day: formatTrendLabel(t.date),
      scans: t.scan_count,
      avgRisk: t.average_risk_score != null ? Math.round(t.average_risk_score) : null,
    }));
  }, [analytics]);

  const distribution = analytics?.risk_level_distribution ?? [];
  const hasChart = chartData.some((d) => d.scans > 0 || d.avgRisk != null);

  return (
    <OverviewWidget
      title="Risk trend summary"
      description="Paste scan volume and average risk score (30 days)"
      action="Analytics"
      actionHref="/dashboard/risk"
      loading={loading}
      empty={
        <OverviewEmptyState
          message="Run security scans to build risk trends and severity distribution."
          action="New scan"
          actionHref="/dashboard/scan"
        />
      }
    >
      {analytics && (hasChart || distribution.length > 0) ? (
        <div className="space-y-5">
          <div className="flex flex-wrap items-end gap-4">
            <div>
              <p className="text-xs uppercase tracking-wider text-[var(--st-fg-muted)]">Avg risk score</p>
              <p className="text-3xl font-semibold tabular-nums text-[var(--st-fg)]">
                {analytics.average_risk_score != null
                  ? Math.round(analytics.average_risk_score)
                  : "—"}
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              {distribution.length > 0 ? (
                distribution.map((r) => (
                  <Badge key={r.risk_level} variant="outline" className="normal-case tabular-nums">
                    {r.risk_level}: {r.count}
                  </Badge>
                ))
              ) : (
                <span className="text-xs text-[var(--st-fg-muted)]">No risk distribution yet</span>
              )}
            </div>
          </div>

          {hasChart ? (
            <div className="h-[220px] w-full min-h-[200px]">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={GRID} vertical={false} />
                  <XAxis dataKey="day" stroke={AXIS} tick={{ fill: AXIS, fontSize: 10 }} axisLine={{ stroke: GRID }} />
                  <YAxis
                    yAxisId="left"
                    stroke={AXIS}
                    tick={{ fill: AXIS, fontSize: 10 }}
                    axisLine={{ stroke: GRID }}
                    allowDecimals={false}
                  />
                  <YAxis
                    yAxisId="right"
                    orientation="right"
                    stroke={AXIS}
                    tick={{ fill: AXIS, fontSize: 10 }}
                    axisLine={{ stroke: GRID }}
                    domain={[0, 100]}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#0f172a",
                      border: "1px solid rgba(148, 163, 184, 0.2)",
                      borderRadius: 8,
                      fontSize: 12,
                      color: "#e2e8f0",
                    }}
                  />
                  <Bar
                    yAxisId="left"
                    dataKey="scans"
                    name="Scans"
                    fill="#22d3ee"
                    radius={[4, 4, 0, 0]}
                    maxBarSize={32}
                  />
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="avgRisk"
                    name="Avg risk"
                    stroke="#fbbf24"
                    strokeWidth={2}
                    dot={{ r: 3, fill: "#fbbf24" }}
                    connectNulls
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className="text-sm text-[var(--st-fg-muted)]">Trend chart populates after daily scan activity.</p>
          )}
        </div>
      ) : null}
    </OverviewWidget>
  );
}
