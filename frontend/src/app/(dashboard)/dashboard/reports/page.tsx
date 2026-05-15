"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { FileText, Plus } from "lucide-react";

import { PageHeader } from "@/components/dashboard/page-header";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { apiFetch, ApiError } from "@/lib/api/client";
import { useAuth } from "@/providers/auth-provider";

type ReportSummary = {
  id: string;
  title: string;
  status: string;
  period_start: string | null;
  period_end: string | null;
  created_at: string;
  downloadable: boolean;
};

type ListResponse = {
  items: ReportSummary[];
  total: number;
};

type GenerateResponse = { id: string; title: string; status: string };

export default function ReportsPage() {
  const { role, hydrated } = useAuth();
  const isAdmin = role === "admin";
  const [data, setData] = useState<ListResponse | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setNotice(null);
    try {
      const res = await apiFetch<ListResponse>("reports?limit=50&offset=0");
      setData(res);
    } catch (e) {
      setData(null);
      setNotice(e instanceof ApiError ? e.message : "Failed to load reports.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    void load();
  }, [hydrated, load]);

  async function generateReport() {
    setBusy(true);
    setNotice(null);
    try {
      await apiFetch<GenerateResponse>("reports/generate", { method: "POST", json: {} });
      await load();
      setNotice("Report generated successfully.");
    } catch (e) {
      setNotice(e instanceof ApiError ? e.message : "Generation failed.");
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
        title="Reports"
        description="AI governance PDFs with usage, risk, PII, and ADM summaries — retained for audit history."
        actions={
          isAdmin ? (
            <Button type="button" variant="secondary" className="h-9 gap-2 px-3" onClick={() => void generateReport()} disabled={busy}>
              <Plus className="h-4 w-4" aria-hidden />
              {busy ? "Generating…" : "New report"}
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

      <div className="overflow-hidden rounded-xl border border-[var(--st-border)] bg-[var(--st-surface)] shadow-sm">
        <div className="flex items-center justify-between border-b border-[var(--st-border)] px-5 py-4">
          <div className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-cyan-400/80" aria-hidden />
            <h2 className="text-sm font-semibold text-[var(--st-fg)]">History</h2>
            {data ? (
              <span className="text-xs text-[var(--st-fg-muted)]">({data.total})</span>
            ) : null}
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[720px] text-left text-sm">
            <thead className="border-b border-[var(--st-border)] bg-[var(--st-muted)]/50 text-xs uppercase tracking-wider text-[var(--st-fg-muted)]">
              <tr>
                <th className="px-5 py-3 font-medium">Title</th>
                <th className="px-5 py-3 font-medium">Status</th>
                <th className="px-5 py-3 font-medium">Period</th>
                <th className="px-5 py-3 font-medium">Created</th>
                <th className="px-5 py-3 font-medium text-right"> </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--st-border)]">
              {loading ? (
                Array.from({ length: 6 }).map((_, i) => (
                  <tr key={i}>
                    <td className="px-5 py-3" colSpan={5}>
                      <Skeleton className="h-9 w-full" />
                    </td>
                  </tr>
                ))
              ) : !data || data.items.length === 0 ? (
                <tr>
                  <td className="px-5 py-14 text-center text-[var(--st-fg-muted)]" colSpan={5}>
                    No reports yet. Generate a compliance pack as an administrator.
                  </td>
                </tr>
              ) : (
                data.items.map((row) => (
                  <tr key={row.id} className="hover:bg-[var(--st-muted)]/40">
                    <td className="px-5 py-3 font-medium text-[var(--st-fg)]">{row.title}</td>
                    <td className="px-5 py-3">
                      <Badge variant={row.status === "ready" ? "success" : row.status === "failed" ? "danger" : "outline"}>
                        {row.status}
                      </Badge>
                    </td>
                    <td className="px-5 py-3 text-[var(--st-fg-muted)]">
                      {row.period_start && row.period_end
                        ? `${new Date(row.period_start).toLocaleDateString()} – ${new Date(row.period_end).toLocaleDateString()}`
                        : "—"}
                    </td>
                    <td className="whitespace-nowrap px-5 py-3 text-[var(--st-fg-muted)]">
                      {new Date(row.created_at).toLocaleString()}
                    </td>
                    <td className="px-5 py-3 text-right">
                      <Link
                        href={`/dashboard/reports/${row.id}`}
                        className="text-xs font-semibold text-[var(--st-accent)] hover:underline"
                      >
                        Open
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
