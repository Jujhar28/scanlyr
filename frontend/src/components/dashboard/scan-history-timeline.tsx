"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ChevronRight, ScanSearch } from "lucide-react";

import { RiskBadge } from "@/components/intel";
import { ButtonLink } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import type { RiskLevel, ScanHistorySummary } from "@/lib/api/scan-history";
import { cn } from "@/lib/utils/cn";

const FILTERS: { label: string; value: RiskLevel | "all" }[] = [
  { label: "All", value: "all" },
  { label: "Critical", value: "critical" },
  { label: "High", value: "high" },
  { label: "Medium", value: "medium" },
  { label: "Low", value: "low" },
];

function contentLabel(type: ScanHistorySummary["content_type"]) {
  if (type === "prompt") return "Prompt";
  if (type === "output") return "Output";
  return "Full scan";
}

export function ScanHistoryTimeline({
  rows,
  loading,
  riskFilter,
  onRiskFilterChange,
}: {
  rows: ScanHistorySummary[];
  loading?: boolean;
  riskFilter: RiskLevel | "all";
  onRiskFilterChange: (v: RiskLevel | "all") => void;
}) {
  if (loading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-24 w-full rounded-2xl" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {FILTERS.map((f) => (
          <button
            key={f.value}
            type="button"
            onClick={() => onRiskFilterChange(f.value)}
            className={cn(
              "rounded-full border px-3 py-1.5 text-xs font-semibold transition",
              riskFilter === f.value
                ? "border-[var(--st-accent)] bg-[var(--st-accent-subtle)] text-[var(--st-accent)]"
                : "border-[var(--st-border)] bg-white text-[var(--st-fg-muted)] hover:border-[var(--st-accent)]/30",
            )}
          >
            {f.label}
          </button>
        ))}
      </div>

      {!rows.length ? (
        <div className="rounded-2xl border border-dashed border-[var(--st-border)] bg-white p-12 text-center">
          <ScanSearch className="mx-auto h-10 w-10 text-[var(--st-accent)]/50" aria-hidden />
          <p className="mt-4 text-sm text-[var(--st-fg-muted)]">No scans match this filter.</p>
          <ButtonLink href="/dashboard/scan" className="mt-4 h-9 px-4 text-sm">
            Run a scan
          </ButtonLink>
        </div>
      ) : (
        <ol className="relative space-y-0">
          <div className="absolute bottom-4 left-[1.15rem] top-4 w-px bg-gradient-to-b from-[var(--st-accent)] via-[var(--st-accent-secondary)]/40 to-transparent" />
          {rows.map((row, i) => (
            <motion.li
              key={row.id}
              initial={{ opacity: 0, x: -12 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05, duration: 0.35 }}
            >
              <Link
                href={`/dashboard/history/${row.id}`}
                className="group relative flex gap-4 rounded-2xl border border-transparent py-3 pl-0 pr-2 transition hover:border-[var(--st-border)] hover:bg-white/80"
              >
                <span className="relative z-10 mt-3 flex h-9 w-9 shrink-0 items-center justify-center rounded-full border-2 border-white bg-[var(--st-accent)] text-white shadow-md shadow-cyan-500/30 ring-4 ring-[var(--st-canvas)]">
                  <span className="font-display text-xs font-bold tabular-nums">{row.risk_score}</span>
                </span>
                <div className="min-w-0 flex-1 rounded-xl border border-[var(--st-border)] bg-white p-4 shadow-sm transition group-hover:shadow-[var(--st-shadow-lg)]">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <RiskBadge level={row.risk_level} />
                      <span className="text-xs font-medium text-[var(--st-fg-muted)]">
                        {contentLabel(row.content_type)}
                      </span>
                    </div>
                    <time className="text-xs text-[var(--st-fg-muted)]">
                      {new Date(row.scanned_at).toLocaleString()}
                    </time>
                  </div>
                  <p className="mt-2 line-clamp-2 font-mono text-xs text-[var(--st-fg-muted)]">
                    {row.input_preview || "—"}
                  </p>
                  <p className="mt-2 flex items-center gap-1 text-xs font-semibold text-[var(--st-accent)] opacity-0 transition group-hover:opacity-100">
                    View full assessment
                    <ChevronRight className="h-3.5 w-3.5" aria-hidden />
                  </p>
                </div>
              </Link>
            </motion.li>
          ))}
        </ol>
      )}
    </div>
  );
}
