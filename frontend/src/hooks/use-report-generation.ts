"use client";

import { useCallback, useState } from "react";

import { apiFetch, ApiError } from "@/lib/api/client";
import { downloadReportPdf, generateReport, type GenerateReportResponse } from "@/lib/api/reports";

export type ReportGenerationPhase =
  | "idle"
  | "checking"
  | "generating"
  | "downloading"
  | "done"
  | "error";

const PHASE_PROGRESS: Record<ReportGenerationPhase, number> = {
  idle: 0,
  checking: 20,
  generating: 65,
  downloading: 90,
  done: 100,
  error: 0,
};

export function useReportGeneration() {
  const [phase, setPhase] = useState<ReportGenerationPhase>("idle");
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<GenerateReportResponse | null>(null);

  const reset = useCallback(() => {
    setPhase("idle");
    setError(null);
    setResult(null);
  }, []);

  const run = useCallback(async (options?: { autoDownload?: boolean }) => {
    const autoDownload = options?.autoDownload ?? true;
    setError(null);
    setResult(null);

    try {
      setPhase("checking");
      const detections = await apiFetch<{ total: number }>("detections?limit=1&offset=0");
      if (detections.total < 1) {
        throw new ApiError(
          "No AI detection events yet. Connect Microsoft 365 and run a full scan before generating a report.",
          422,
          null,
        );
      }

      setPhase("generating");
      const report = await generateReport();
      setResult(report);

      if (autoDownload && report.status === "ready") {
        setPhase("downloading");
        await downloadReportPdf(report.id, `${slugify(report.title)}.pdf`);
      }

      setPhase("done");
      return report;
    } catch (e) {
      const message =
        e instanceof ApiError
          ? e.message
          : e instanceof Error
            ? e.message
            : "Report generation failed.";
      setError(message);
      setPhase("error");
      throw e;
    }
  }, []);

  const isRunning =
    phase === "checking" || phase === "generating" || phase === "downloading";

  return {
    phase,
    progress: PHASE_PROGRESS[phase],
    error,
    result,
    isRunning,
    run,
    reset,
  };
}

function slugify(title: string): string {
  return title
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 80) || "scanlyr-report";
}
