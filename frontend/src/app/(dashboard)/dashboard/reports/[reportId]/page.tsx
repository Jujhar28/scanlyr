"use client";

import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

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
import { apiFetch, apiFetchBlob, ApiError } from "@/lib/api/client";
import { useAuth } from "@/providers/auth-provider";

type ReportDetail = {
  id: string;
  title: string;
  report_type: string;
  status: string;
  period_start: string | null;
  period_end: string | null;
  created_at: string;
  updated_at: string;
  created_by_user_id: string | null;
  error_message: string | null;
  downloadable: boolean;
  meta: {
    sections?: Record<string, unknown>;
    version?: number;
    algorithm?: string;
  } | null;
};

export default function ReportDetailPage() {
  const params = useParams();
  const reportId = typeof params.reportId === "string" ? params.reportId : "";
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
      const res = await apiFetch<ReportDetail>(`reports/${reportId}`);
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
    if (!reportId) return;
    setDownloading(true);
    setError(null);
    try {
      const blob = await apiFetchBlob(`reports/${reportId}/download`);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `scanlyr-ai-governance-${reportId}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Download failed.");
    } finally {
      setDownloading(false);
    }
  }

  if (!hydrated) {
    return null;
  }

  const sections = row?.meta?.sections;

  return (
    <div className="mx-auto max-w-[1600px] space-y-6">
      <div className="flex flex-wrap items-center gap-3">
        <ButtonLink href="/dashboard/reports" variant="ghost" className="h-9 px-3 text-sm">
          ← Reports
        </ButtonLink>
      </div>

      {loading ? (
        <div className="space-y-4">
          <Skeleton className="h-10 w-2/3 max-w-md rounded-lg" />
          <Skeleton className="h-32 w-full rounded-xl" />
          <Skeleton className="h-64 w-full rounded-xl" />
        </div>
      ) : null}

      {error ? (
        <p className="text-sm text-red-200" role="alert">
          {error}
        </p>
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
                <Badge variant={row.status === "ready" ? "success" : row.status === "failed" ? "danger" : "outline"}>
                  {row.status}
                </Badge>
                {row.downloadable ? (
                  <button
                    type="button"
                    onClick={() => void downloadPdf()}
                    disabled={downloading}
                    className="inline-flex h-9 items-center justify-center rounded-lg bg-[var(--st-accent)] px-4 text-sm font-medium text-[#041018] hover:opacity-90 disabled:opacity-50"
                  >
                    {downloading ? "Downloading…" : "Download PDF"}
                  </button>
                ) : null}
              </div>
            }
          />

          <Card className="border-[var(--st-border)] bg-[var(--st-surface)] shadow-sm">
            <CardHeader className="border-b border-[var(--st-border)] bg-[var(--st-muted)]/30">
              <CardTitle>Delivery</CardTitle>
              <CardDescription>PDF availability and pipeline errors.</CardDescription>
            </CardHeader>
            <div className="p-6">
              {!row.downloadable ? (
                <p className="text-sm text-[var(--st-fg-muted)]">
                  PDF is not available (report may still be rendering or failed).
                </p>
              ) : (
                <p className="text-sm text-[var(--st-fg-muted)]">Use Download PDF to fetch the signed file.</p>
              )}
              {row.error_message ? <p className="mt-3 text-sm text-red-200">{row.error_message}</p> : null}
            </div>
          </Card>

          {sections ? (
            <Card className="border-[var(--st-border)] bg-[var(--st-surface)] shadow-sm">
              <CardHeader>
                <CardTitle>Sections snapshot</CardTitle>
                <CardDescription>
                  Same structure as the PDF: usage, risk, PII, users, ADM, and recommendations.
                </CardDescription>
              </CardHeader>
              <div className="px-6 pb-6">
                <pre className="max-h-[32rem] overflow-auto rounded-lg bg-black/30 p-3 text-xs text-[var(--st-fg-muted)]">
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
