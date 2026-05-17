"use client";

import Link from "next/link";
import { useState } from "react";
import { Download, ExternalLink, FileText, Loader2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError } from "@/lib/api/client";
import { downloadReportPdf, type ReportSummary } from "@/lib/api/reports";
import { useToast } from "@/providers/toast-provider";

function statusVariant(status: string): "success" | "danger" | "outline" | "warning" {
  if (status === "ready") return "success";
  if (status === "failed") return "danger";
  if (status === "pending" || status === "generating") return "warning";
  return "outline";
}

export function ReportsList({
  items,
  total,
  loading,
}: {
  items: ReportSummary[];
  total: number;
  loading?: boolean;
}) {
  const { toast } = useToast();
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  function safePdfFilename(title: string): string {
    const normalized = title.normalize("NFC").trim().slice(0, 120);
    const sanitized = normalized
      .replace(/[<>:"/\\|?*\x00-\x1f]/g, "")
      .replace(/\s+/g, "-")
      .replace(/-+/g, "-")
      .replace(/^-+|-+$/g, "");
    const base = sanitized || "scanlyr-report";
    return `${base}.pdf`;
  }

  async function handleDownload(row: ReportSummary) {
    setDownloadingId(row.id);
    try {
      await downloadReportPdf(row.id, safePdfFilename(row.title));
      toast({
        variant: "success",
        title: "Download started",
        description: row.title,
      });
    } catch (e) {
      toast({
        variant: "error",
        title: "Download failed",
        description: e instanceof ApiError ? e.message : "Could not download PDF.",
      });
    } finally {
      setDownloadingId(null);
    }
  }

  return (
    <section className="overflow-hidden rounded-xl border border-[var(--st-border)] bg-[var(--st-surface)] shadow-sm">
      <header className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--st-border)] px-5 py-4">
        <div className="flex items-center gap-2">
          <FileText className="h-5 w-5 text-[var(--st-accent)]" aria-hidden />
          <h2 className="text-sm font-semibold text-[var(--st-fg)]">Report history</h2>
          {!loading ? (
            <span className="text-xs text-[var(--st-fg-muted)]">({total})</span>
          ) : null}
        </div>
      </header>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[760px] text-left text-sm">
          <thead className="border-b border-[var(--st-border)] bg-[var(--st-muted)]/50 text-xs uppercase tracking-wider text-[var(--st-fg-muted)]">
            <tr>
              <th className="px-5 py-3 font-medium">Title</th>
              <th className="px-5 py-3 font-medium">Status</th>
              <th className="px-5 py-3 font-medium">Period</th>
              <th className="px-5 py-3 font-medium">Created</th>
              <th className="px-5 py-3 font-medium text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--st-border)]">
            {loading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={i}>
                  <td className="px-5 py-3" colSpan={5}>
                    <Skeleton className="h-10 w-full rounded-md" />
                  </td>
                </tr>
              ))
            ) : items.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-5 py-12 text-center text-[var(--st-fg-muted)]">
                  No reports generated yet. Use Generate Report above to create your first PDF.
                </td>
              </tr>
            ) : (
              items.map((row) => (
                <tr key={row.id} className="transition hover:bg-[var(--st-muted)]/40">
                  <td className="px-5 py-3 font-medium text-[var(--st-fg)]">{row.title}</td>
                  <td className="px-5 py-3">
                    <Badge variant={statusVariant(row.status)} className="normal-case">
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
                  <td className="px-5 py-3">
                    <div className="flex items-center justify-end gap-2">
                      {row.downloadable ? (
                        <button
                          type="button"
                          disabled={downloadingId === row.id}
                          onClick={() => void handleDownload(row)}
                          className="inline-flex h-8 items-center gap-1.5 rounded-lg border border-[var(--st-border)] bg-[var(--st-muted)]/50 px-2.5 text-xs font-medium text-[var(--st-fg)] hover:bg-[var(--st-muted)] disabled:opacity-50"
                        >
                          {downloadingId === row.id ? (
                            <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden />
                          ) : (
                            <Download className="h-3.5 w-3.5" aria-hidden />
                          )}
                          PDF
                        </button>
                      ) : null}
                      <Link
                        href={`/dashboard/reports/${row.id}`}
                        className="inline-flex h-8 items-center gap-1 rounded-lg px-2.5 text-xs font-semibold text-[var(--st-accent)] hover:underline"
                      >
                        <ExternalLink className="h-3.5 w-3.5" aria-hidden />
                        Details
                      </Link>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
