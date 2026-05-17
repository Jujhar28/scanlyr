"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { RefreshCw } from "lucide-react";

import { ScanHistoryTimeline } from "@/components/dashboard/scan-history-timeline";
import { IntelCard, PageHero } from "@/components/intel";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ApiError } from "@/lib/api/client";
import {
  fetchAllScanHistory,
  sortScanHistoryNewestFirst,
  type RiskLevel,
  type ScanHistorySummary,
} from "@/lib/api/scan-history";
import { useAuth } from "@/providers/auth-provider";

const SCAN_HISTORY_MAX = 200;

export default function HistoryPage() {
  const { hydrated } = useAuth();
  const [rows, setRows] = useState<ScanHistorySummary[]>([]);
  const [total, setTotal] = useState(0);
  const [truncated, setTruncated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [riskFilter, setRiskFilter] = useState<RiskLevel | "all">("all");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchAllScanHistory({ maxItems: SCAN_HISTORY_MAX });
      setRows(res.items);
      setTotal(res.total);
      setTruncated(res.truncated);
    } catch (e) {
      setRows([]);
      setError(e instanceof ApiError ? e.message : "Failed to load scan history.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    void load();
  }, [hydrated, load]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    let base = sortScanHistoryNewestFirst(rows);
    if (riskFilter !== "all") {
      base = base.filter((r) => r.risk_level === riskFilter);
    }
    if (!q) return base;
    return base.filter(
      (r) =>
        r.input_preview.toLowerCase().includes(q) ||
        r.content_type.toLowerCase().includes(q) ||
        r.risk_level.toLowerCase().includes(q),
    );
  }, [rows, query, riskFilter]);

  if (!hydrated) return null;

  return (
    <div className="mx-auto max-w-[1680px] space-y-6 pb-10">
      <PageHero
        eyebrow="Intelligence log"
        title="Scan history"
        description="Timeline of paste-to-scan assessments. Open any entry for the full explainable report."
        actions={
          <Button type="button" variant="secondary" className="h-9 gap-2 px-3" onClick={() => void load()}>
            <RefreshCw className="h-4 w-4" aria-hidden />
            Refresh
          </Button>
        }
      />

      {error ? (
        <motion.div
          role="alert"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-xl border border-rose-500/30 bg-rose-50 px-4 py-3 text-sm text-rose-800"
        >
          {error}
        </motion.div>
      ) : null}

      {!loading && !error && truncated ? (
        <p role="status" className="text-sm text-[var(--st-fg-muted)]">
          Showing the {rows.length} most recent of {total} scans.
        </p>
      ) : null}

      <IntelCard title="Search" description="Filter the timeline" accent="cyan">
        <Input
          placeholder="Search preview, type, or risk level…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="max-w-lg rounded-xl border-[var(--st-border-strong)] bg-white"
          disabled={loading}
        />
      </IntelCard>

      <IntelCard title="Timeline" accent="indigo" noPadding>
        <div className="p-5">
          <ScanHistoryTimeline
            rows={filtered}
            loading={loading}
            riskFilter={riskFilter}
            onRiskFilterChange={setRiskFilter}
          />
        </div>
      </IntelCard>
    </div>
  );
}
