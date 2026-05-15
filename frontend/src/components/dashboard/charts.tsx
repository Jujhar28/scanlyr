"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const GRID = "rgba(148, 163, 184, 0.08)";
const AXIS = "#64748b";
const TOOLTIP_BG = "#0f172a";
const TOOLTIP_BORDER = "rgba(148, 163, 184, 0.2)";

const SEVERITY_COLORS: Record<string, string> = {
  critical: "#f87171",
  high: "#fb923c",
  medium: "#fbbf24",
  low: "#94a3b8",
  info: "#64748b",
};

type SeverityDatum = { name: string; value: number };

export function SeverityDonut({ data }: { data: SeverityDatum[] }) {
  const total = data.reduce((s, d) => s + d.value, 0);
  if (total === 0) {
    return (
      <div className="flex h-[220px] items-center justify-center rounded-lg border border-[var(--st-border)] bg-[var(--st-muted)]/30 text-sm text-[var(--st-fg-muted)]">
        No severity data yet
      </div>
    );
  }
  return (
    <div className="h-[220px] w-full min-h-[220px]">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            innerRadius={52}
            outerRadius={72}
            paddingAngle={2}
          >
            {data.map((entry) => (
              <Cell
                key={entry.name}
                fill={SEVERITY_COLORS[entry.name.toLowerCase()] ?? "#64748b"}
                stroke="transparent"
              />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              backgroundColor: TOOLTIP_BG,
              border: `1px solid ${TOOLTIP_BORDER}`,
              borderRadius: 8,
              fontSize: 12,
              color: "#e2e8f0",
            }}
            formatter={(value) => [`${value ?? 0}`, "Events"]}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

type ToolDatum = { name: string; count: number };

export function ToolBarChart({ data }: { data: ToolDatum[] }) {
  if (!data.length) {
    return (
      <div className="flex h-[240px] items-center justify-center rounded-lg border border-[var(--st-border)] bg-[var(--st-muted)]/30 text-sm text-[var(--st-fg-muted)]">
        No tool distribution yet
      </div>
    );
  }
  return (
    <div className="h-[240px] w-full min-h-[240px]">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={GRID} horizontal={false} />
          <XAxis type="number" stroke={AXIS} tick={{ fill: AXIS, fontSize: 11 }} axisLine={{ stroke: GRID }} />
          <YAxis
            type="category"
            dataKey="name"
            width={100}
            stroke={AXIS}
            tick={{ fill: AXIS, fontSize: 11 }}
            axisLine={{ stroke: GRID }}
          />
          <Tooltip
            cursor={{ fill: "rgba(0, 200, 255, 0.06)" }}
            contentStyle={{
              backgroundColor: TOOLTIP_BG,
              border: `1px solid ${TOOLTIP_BORDER}`,
              borderRadius: 8,
              fontSize: 12,
              color: "#e2e8f0",
            }}
            formatter={(value) => [`${value ?? 0}`, "Count"]}
          />
          <Bar dataKey="count" fill="#22d3ee" radius={[0, 4, 4, 0]} maxBarSize={22} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

type TrendDatum = { day: string; count: number };

export function EventTrendChart({ data }: { data: TrendDatum[] }) {
  if (!data.length) {
    return (
      <div className="flex h-[240px] items-center justify-center rounded-lg border border-[var(--st-border)] bg-[var(--st-muted)]/30 text-sm text-[var(--st-fg-muted)]">
        No timeline yet
      </div>
    );
  }
  return (
    <div className="h-[240px] w-full min-h-[240px]">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={GRID} vertical={false} />
          <XAxis dataKey="day" stroke={AXIS} tick={{ fill: AXIS, fontSize: 10 }} axisLine={{ stroke: GRID }} />
          <YAxis stroke={AXIS} tick={{ fill: AXIS, fontSize: 11 }} axisLine={{ stroke: GRID }} allowDecimals={false} />
          <Tooltip
            contentStyle={{
              backgroundColor: TOOLTIP_BG,
              border: `1px solid ${TOOLTIP_BORDER}`,
              borderRadius: 8,
              fontSize: 12,
              color: "#e2e8f0",
            }}
          />
          <Bar dataKey="count" fill="#38bdf8" radius={[4, 4, 0, 0]} maxBarSize={40} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
