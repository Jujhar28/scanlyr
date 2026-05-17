"use client";

import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { Download, Loader2 } from "lucide-react";

import { ButtonLink } from "@/components/ui/button";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { PageHeader } from "@/components/dashboard/page-header";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError } from "@/lib/api/client";
import { downloadReportPdf, getReport, type ReportDetail } from "@/lib/api/reports";
import { useToast } from "@/providers/toast-provider";
import { useAuth } from "@/providers/auth-provider";

function statusVariant(status: string): "success" | "danger" | "outline" | "warning" {
  if (status === "ready") return "success";
  if (status === "failed") return "danger";
  if (status === "pending" || status === "generating") return "warning";
  return "outline";
}

export default function ReportDetailPage() {
  const params = useParams();
  const reportId = typeof params.reportId === "string" ? params.reportId : "";
  const { toast } = useToast();
  const { hydrated } = useAuth();
  const [row, setRow] = useState<ReportDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);

  const load = useCallback(async () => {
    if (!reportId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await getReport(reportId);
      setRow(res);
    } catch (e) {
      setRow(null);
      setError(e instanceof ApiError ? e.message : "Failed to load report.");
    } finally {
      setLoading(false);
    }
  }, [reportId]);

  useEffect(() => {
    if (!hydrated || !reportId) return;
    void load();
  }, [hydrated, reportId, load]);

  async function downloadPdf() {
    if (!reportId || !row) return;
    setDownloading(true);
    setError(null);
    try {
      await downloadReportPdf(
        reportId,
        `${row.title.replace(/\s+/g, "-").toLowerCase()}.pdf`,
      );
      toast({
        variant: "success",
        title: "Download started",
        description: row.title,
      });
    } catch (e) {
      const message = e instanceof ApiError ? e.message : "Download failed.";
      setError(message);
      toast({
        variant: "error",
        title: "Download failed",
        description: message,
      });
    } finally {
      setDownloading(false);
    }
  }

  if (!hydrated) {
    return null;
  }

  const sections = row?.meta?.sections;

  return (
    <div className="mx-auto max-w-[1600px] space-y-6 pb-8">
      <ButtonLink href="/dashboard/reports" variant="ghost" className="h-9 px-3 text-sm">
        ← Reports
      </ButtonLink>

      {loading ? (
        <div className="space-y-4">
          <Skeleton className="h-10 w-2/3 max-w-md rounded-lg" />
          <Skeleton className="h-32 w-full rounded-xl" />
          <Skeleton className="h-64 w-full rounded-xl" />
        </div>
      ) : null}

      {error && !row ? (
        <div role="alert" className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-100">
          {error}
        </div>
      ) : null}

      {row ? (
        <>
          <PageHeader
            title={row.title}
            description={
              row.period_start && row.period_end
                ? `${new Date(row.period_start).toLocaleString()} – ${new Date(row.period_end).toLocaleString()}`
                : "Compliance governance export"
            }
            actions={
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant={statusVariant(row.status)} className="normal-case">
                  {row.status}
                </Badge>
                {row.downloadable ? (
                  <button
                    type="button"
                    onClick={() => void downloadPdf()}
                    disabled={downloading}
                    className="inline-flex h-10 items-center gap-2 rounded-lg bg-[var(--st-accent)] px-4 text-sm font-semibold text-white hover:opacity-90 disabled:opacity-50"
                  >
                    {downloading ? (
                      <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
                    ) : (
                      <Download className="h-4 w-4" aria-hidden />
                    )}
                    {downloading ? "Downloading…" : "Download PDF"}
                  </button>
                ) : null}
              </div>
            }
          />

          <div className="grid gap-6 lg:grid-cols-2">
            <Card className="border-[var(--st-border)] bg-[var(--st-surface)] shadow-sm">
              <CardHeader className="border-b border-[var(--st-border)] bg-[var(--st-muted)]/30">
                <CardTitle className="text-base">Delivery</CardTitle>
                <CardDescription>PDF file and generation status.</CardDescription>
              </CardHeader>
              <div className="space-y-3 p-6 text-sm">
                <p className="text-[var(--st-fg-muted)]">
                  {row.downloadable
                    ? "PDF is stored and ready to download."
                    : "PDF is not available — the report may still be processing or failed."}
                </p>
                {row.error_message ? (
                  <p className="rounded-lg border border-red-500/25 bg-red-500/10 px-3 py-2 text-red-100">
                    {row.error_message}
                  </p>
                ) : null}
                <dl className="grid gap-2 text-xs text-[var(--st-fg-muted)]">
                  <div className="flex justify-between gap-4">
                    <dt>Report ID</dt>
                    <dd className="font-mono text-[var(--st-fg)]">{row.id}</dd>
                  </div>
                  <div className="flex justify-between gap-4">
                    <dt>Type</dt>
                    <dd className="text-[var(--st-fg)]">{row.report_type}</dd>
                  </div>
                  <div className="flex justify-between gap-4">
                    <dt>Updated</dt>
                    <dd className="tabular-nums text-[var(--st-fg)]">
                      {new Date(row.updated_at).toLocaleString()}
                    </dd>
                  </div>
                </dl>
              </div>
            </Card>

            <Card className="border-[var(--st-border)] bg-[var(--st-surface)] shadow-sm">
              <CardHeader>
                <CardTitle className="text-base">What&apos;s inside</CardTitle>
                <CardDescription>
                  Usage, risk, PII, users, ADM activity, and remediation guidance.
                </CardDescription>
              </CardHeader>
              <div className="p-6 text-sm text-[var(--st-fg-muted)]">
                {sections ? (
                  <p>Section snapshot available below — matches the generated PDF structure.</p>
                ) : (
                  <p>Metadata sections will appear when generation completes successfully.</p>
                )}
              </div>
            </Card>
          </div>

          {sections ? (
            <Card className="border-[var(--st-border)] bg-[var(--st-surface)] shadow-sm">
              <CardHeader>
                <CardTitle className="text-base">Sections snapshot</CardTitle>
                <CardDescription>Structured content included in the PDF export.</CardDescription>
              </CardHeader>
              <div className="px-6 pb-6">
                <pre className="max-h-[28rem] overflow-auto rounded-lg bg-black/30 p-4 text-xs text-[var(--st-fg-muted)]">
                  {JSON.stringify(sections, null, 2)}
                </pre>
              </div>
            </Card>
          ) : null}
        </>
      ) : null}
    </div>
  );
}
