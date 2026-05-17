"use client";

import { useCallback, useEffect, useState } from "react";
import { motion } from "framer-motion";
import { RefreshCw } from "lucide-react";

import { GenerateReportPanel, ReportsList } from "@/components/reports";
import { PageHero } from "@/components/intel";
import { Button } from "@/components/ui/button";
import { useReportGeneration } from "@/hooks/use-report-generation";
import { apiFetch, ApiError } from "@/lib/api/client";
import { listReports, type ReportListResponse } from "@/lib/api/reports";
import { useToast } from "@/providers/toast-provider";
import { useAuth } from "@/providers/auth-provider";

export default function ReportsPage() {
  const { toast } = useToast();
  const { role, hydrated } = useAuth();
  const isAdmin = role === "admin";

  const [data, setData] = useState<ReportListResponse | null>(null);
  const [detectionsTotal, setDetectionsTotal] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [detectionsLoading, setDetectionsLoading] = useState(true);
  const [listError, setListError] = useState<string | null>(null);

  const generation = useReportGeneration();

  const loadReports = useCallback(async () => {
    setLoading(true);
    setListError(null);
    try {
      const res = await listReports(50, 0);
      setData(res);
    } catch (e) {
      setData(null);
      setListError(e instanceof ApiError ? e.message : "Failed to load reports.");
    } finally {
      setLoading(false);
    }
  }, []);

  const loadDetectionsCount = useCallback(async () => {
    setDetectionsLoading(true);
    try {
      const res = await apiFetch<{ total: number }>("detections?limit=1&offset=0");
      setDetectionsTotal(res.total);
    } catch {
      setDetectionsTotal(null);
    } finally {
      setDetectionsLoading(false);
    }
  }, []);

  const reload = useCallback(async () => {
    await Promise.all([loadReports(), loadDetectionsCount()]);
  }, [loadReports, loadDetectionsCount]);

  useEffect(() => {
    if (!hydrated) return;
    void reload();
  }, [hydrated, reload]);

  async function handleGenerate() {
    try {
      const report = await generation.run({ autoDownload: true });
      await loadReports();
      toast({
        variant: "success",
        title: "Report generated",
        description:
          report.status === "ready"
            ? `${report.title} is ready and downloading.`
            : `${report.title} was created with status: ${report.status}.`,
      });
    } catch (e) {
      toast({
        variant: "error",
        title: "Report generation failed",
        description: e instanceof ApiError ? e.message : "Could not generate the compliance PDF.",
      });
    }
  }

  if (!hydrated) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      className="mx-auto max-w-[1680px] space-y-6 pb-10"
    >
      <PageHero
        eyebrow="Compliance"
        title="Reports"
        description="Generate governance PDFs with usage, risk, and recommendations — retained for audit."
        actions={
          <Button
            type="button"
            variant="secondary"
            className="h-9 gap-2 px-3"
            disabled={loading || generation.isRunning}
            onClick={() => void reload()}
          >
            <RefreshCw
              className={loading || generation.isRunning ? "h-4 w-4 animate-spin" : "h-4 w-4"}
              aria-hidden
            />
            Refresh
          </Button>
        }
      />

      {listError ? (
        <div
          role="alert"
          className="rounded-xl border border-rose-500/30 bg-rose-50 px-4 py-3 text-sm text-rose-800"
        >
          {listError}
        </div>
      ) : null}

      <GenerateReportPanel
        isAdmin={isAdmin}
        detectionsTotal={detectionsTotal}
        detectionsLoading={detectionsLoading}
        phase={generation.phase}
        progress={generation.progress}
        error={generation.error}
        isRunning={generation.isRunning}
        onGenerate={handleGenerate}
      />

      <ReportsList items={data?.items ?? []} total={data?.total ?? 0} loading={loading} />
    </motion.div>
  );
}
