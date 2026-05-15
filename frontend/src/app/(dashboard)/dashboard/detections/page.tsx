"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Filter, RefreshCw } from "lucide-react";

import { PageHeader } from "@/components/dashboard/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { apiFetch, ApiError } from "@/lib/api/client";
import { cn } from "@/lib/utils/cn";
import { useAuth } from "@/providers/auth-provider";

type RiskScore = {
  id: string;
  score_kind: string;
  score: string;
};

type DetectionItem = {
  id: string;
  scan_session_id: string | null;
  occurred_at: string;
  source: string;
  tool_name: string | null;
  tool_vendor: string | null;
  channel: string | null;
  severity: string;
  confidence: number | null;
  external_ref: string | null;
  risk_scores: RiskScore[];
};

type ListResponse = {
  items: DetectionItem[];
  total: number;
  limit: number;
  offset: number;
};

type RunResponse = {
  scan_session_id: string;
  events_normalized: number;
  candidates: number;
  inserted: number;
  skipped_duplicates: number;
};

const PAGE_SIZE = 25;
const FETCH_LIMIT = 400;

const SEVERITIES = ["all", "critical", "high", "medium", "low", "info"] as const;

function primaryScore(row: DetectionItem): string {
  const r = row.risk_scores.find((s) => s.score_kind === "detection");
  return r?.score ?? "—";
}

export default function DetectionsPage() {
  const { role, hydrated } = useAuth();
  const isAdmin = role === "admin";
  const [raw, setRaw] = useState<DetectionItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [severity, setSeverity] = useState<(typeof SEVERITIES)[number]>("all");
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(0);

  const load = useCallback(async () => {
    setLoading(true);
    setNotice(null);
    try {
      const res = await apiFetch<ListResponse>(`detections?limit=${FETCH_LIMIT}&offset=0`);
      setRaw(res.items);
      setTotal(res.total);
    } catch (e) {
      setRaw([]);
      setNotice(e instanceof ApiError ? e.message : "Failed to load detections.");
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
    return raw.filter((row) => {
      if (severity !== "all" && row.severity !== severity) return false;
      if (!q) return true;
      const blob = `${row.tool_name ?? ""} ${row.tool_vendor ?? ""} ${row.channel ?? ""} ${row.external_ref ?? ""}`.toLowerCase();
      return blob.includes(q);
    });
  }, [raw, severity, query]);

  useEffect(() => {
    setPage(0);
  }, [severity, query]);

  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const pageSafe = Math.min(page, pageCount - 1);
  const slice = filtered.slice(pageSafe * PAGE_SIZE, pageSafe * PAGE_SIZE + PAGE_SIZE);

  async function runDetection() {
    setBusy(true);
    setNotice(null);
    try {
      const summary = await apiFetch<RunResponse>("detections/run?top=120", { method: "POST" });
      await load();
      setNotice(
        `Last run: ${summary.inserted} new, ${summary.skipped_duplicates} skipped, ${summary.candidates} candidates.`,
      );
    } catch (e) {
      setNotice(e instanceof ApiError ? e.message : "Detection run failed.");
    } finally {
      setBusy(false);
    }
  }

  if (!hydrated) {
    return null;
  }

  return (
    <div className="mx-auto max-w-[1600px] space-y-6">
      <PageHeader
        title="AI events"
        description="Unauthorized or ungoverned AI tool signals from Microsoft 365 telemetry. Filter, triage, and drill into evidence."
        actions={
          isAdmin ? (
            <Button type="button" variant="secondary" className="h-9 gap-2 px-3" onClick={() => void runDetection()} disabled={busy}>
              <RefreshCw className={cn("h-4 w-4", busy && "animate-spin")} aria-hidden />
              {busy ? "Running…" : "Run detection"}
            </Button>
          ) : null
        }
      />

      {notice ? (
        <div
          role="status"
          className="rounded-lg border border-[var(--st-border)] bg-[var(--st-muted)]/60 px-4 py-3 text-sm text-[var(--st-fg)]"
        >
          {notice}
        </div>
      ) : null}

      <div className="flex flex-col gap-4 rounded-xl border border-[var(--st-border)] bg-[var(--st-surface)] p-4 shadow-sm lg:flex-row lg:items-end">
        <div className="grid flex-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div className="space-y-2">
            <Label htmlFor="ai-filter-search" className="text-xs uppercase tracking-wider text-[var(--st-fg-muted)]">
              Search
            </Label>
            <div className="relative">
              <Filter className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--st-fg-muted)]" />
              <Input
                id="ai-filter-search"
                placeholder="Tool, vendor, channel…"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="h-10 border-[var(--st-border)] bg-[var(--st-muted)]/40 pl-9 text-[var(--st-fg)] placeholder:text-[var(--st-fg-muted)]"
              />
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="ai-filter-severity" className="text-xs uppercase tracking-wider text-[var(--st-fg-muted)]">
              Severity
            </Label>
            <select
              id="ai-filter-severity"
              value={severity}
              onChange={(e) => setSeverity(e.target.value as (typeof SEVERITIES)[number])}
              className="h-10 w-full rounded-lg border border-[var(--st-border)] bg-[var(--st-muted)]/40 px-3 text-sm text-[var(--st-fg)] outline-none ring-cyan-500/30 focus:ring-2"
            >
              {SEVERITIES.map((s) => (
                <option key={s} value={s}>
                  {s === "all" ? "All severities" : s}
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-end gap-2 text-sm text-[var(--st-fg-muted)]">
            <span>
              Showing <span className="font-medium text-[var(--st-fg)]">{filtered.length}</span> of{" "}
              <span className="font-medium text-[var(--st-fg)]">{raw.length}</span> loaded
              {total > raw.length ? ` (${total} total in org)` : null}
            </span>
          </div>
        </div>
      </div>

      <div className="overflow-hidden rounded-xl border border-[var(--st-border)] bg-[var(--st-surface)] shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[900px] text-left text-sm">
            <thead className="sticky top-0 z-10 border-b border-[var(--st-border)] bg-[var(--st-muted)]/80 backdrop-blur-sm">
              <tr className="text-xs uppercase tracking-wider text-[var(--st-fg-muted)]">
                <th className="px-4 py-3 font-medium">Time</th>
                <th className="px-4 py-3 font-medium">Tool</th>
                <th className="px-4 py-3 font-medium">Vendor</th>
                <th className="px-4 py-3 font-medium">Severity</th>
                <th className="px-4 py-3 font-medium">Score</th>
                <th className="px-4 py-3 font-medium">Channel</th>
                <th className="px-4 py-3 font-medium text-right"> </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--st-border)]">
              {loading ? (
                Array.from({ length: 8 }).map((_, i) => (
                  <tr key={i}>
                    <td className="px-4 py-3" colSpan={7}>
                      <Skeleton className="h-8 w-full" />
                    </td>
                  </tr>
                ))
              ) : slice.length === 0 ? (
                <tr>
                  <td className="px-4 py-12 text-center text-[var(--st-fg-muted)]" colSpan={7}>
                    No events match filters. Connect Microsoft 365 and run detection, or adjust filters.
                  </td>
                </tr>
              ) : (
                slice.map((row) => (
                  <tr key={row.id} className="transition-colors hover:bg-[var(--st-muted)]/50">
                    <td className="whitespace-nowrap px-4 py-3 text-[var(--st-fg-muted)]">
                      {new Date(row.occurred_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-3 font-medium text-[var(--st-fg)]">{row.tool_name ?? "—"}</td>
                    <td className="px-4 py-3 text-[var(--st-fg-muted)]">{row.tool_vendor ?? "—"}</td>
                    <td className="px-4 py-3">
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
                    <td className="px-4 py-3 tabular-nums text-[var(--st-fg-muted)]">{primaryScore(row)}</td>
                    <td className="max-w-[180px] truncate px-4 py-3 text-[var(--st-fg-muted)]">{row.channel ?? "—"}</td>
                    <td className="px-4 py-3 text-right">
                      <Link
                        href={`/dashboard/detections/${row.id}`}
                        className="text-xs font-semibold text-[var(--st-accent)] hover:underline"
                      >
                        Details
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {!loading && filtered.length > PAGE_SIZE ? (
          <div className="flex flex-wrap items-center justify-between gap-3 border-t border-[var(--st-border)] px-4 py-3">
            <p className="text-xs text-[var(--st-fg-muted)]">
              Page {pageSafe + 1} of {pageCount}
            </p>
            <div className="flex gap-2">
              <Button
                type="button"
                variant="secondary"
                className="h-8 px-3 text-xs"
                disabled={pageSafe <= 0}
                onClick={() => setPage((p) => Math.max(0, p - 1))}
              >
                Previous
              </Button>
              <Button
                type="button"
                variant="secondary"
                className="h-8 px-3 text-xs"
                disabled={pageSafe >= pageCount - 1}
                onClick={() => setPage((p) => Math.min(pageCount - 1, p + 1))}
              >
                Next
              </Button>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
