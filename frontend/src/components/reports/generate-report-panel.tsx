"use client";

import Link from "next/link";
import { FileText, Loader2, Radar } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import type { ReportGenerationPhase } from "@/hooks/use-report-generation";
import { cn } from "@/lib/utils/cn";

function phaseLabel(phase: ReportGenerationPhase): string {
  switch (phase) {
    case "checking":
      return "Checking detection data…";
    case "generating":
      return "Building compliance PDF from tenant signals…";
    case "downloading":
      return "Preparing download…";
    case "done":
      return "Report ready.";
    case "error":
      return "Generation failed.";
    default:
      return "Export AI governance summary with usage, risk, PII, and recommendations.";
  }
}

export function GenerateReportPanel({
  isAdmin,
  detectionsTotal,
  detectionsLoading,
  phase,
  progress,
  error,
  isRunning,
  onGenerate,
}: {
  isAdmin: boolean;
  detectionsTotal: number | null;
  detectionsLoading?: boolean;
  phase: ReportGenerationPhase;
  progress: number;
  error: string | null;
  isRunning: boolean;
  onGenerate: () => void | Promise<void>;
}) {
  const noDetections = detectionsTotal === 0;
  const detectionsUnknown = detectionsTotal === null && !detectionsLoading;

  return (
    <section className="overflow-hidden rounded-xl border border-[var(--st-accent)]/30 bg-gradient-to-br from-[var(--st-surface)] to-[var(--st-muted)]/40 shadow-sm">
      <div className="flex flex-col gap-5 p-6 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex min-w-0 items-start gap-4">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-[var(--st-accent)]/15 text-[var(--st-accent)]">
            <FileText className="h-6 w-6" aria-hidden />
          </div>
          <div className="min-w-0">
            <h2 className="text-lg font-semibold text-[var(--st-fg)]">Generate Report</h2>
            <p className="mt-1 text-sm text-[var(--st-fg-muted)]">{phaseLabel(phase)}</p>
            {detectionsTotal != null && !detectionsLoading ? (
              <p className="mt-2 text-xs text-[var(--st-fg-muted)]">
                {detectionsTotal} AI event{detectionsTotal === 1 ? "" : "s"} available for this export
              </p>
            ) : null}
          </div>
        </div>

        {isAdmin ? (
          <Button
            type="button"
            className="h-11 shrink-0 px-6 text-base font-semibold"
            disabled={isRunning || detectionsLoading || noDetections}
            onClick={() => void onGenerate()}
          >
            {isRunning ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin" aria-hidden />
                Generating…
              </>
            ) : (
              "Generate Report"
            )}
          </Button>
        ) : (
          <p className="text-sm text-[var(--st-fg-muted)]">Administrators can generate reports.</p>
        )}
      </div>

      {isRunning || phase === "done" ? (
        <div className="border-t border-[var(--st-border)]/80 px-6 pb-6">
          <Progress value={progress} className="h-2" />
          <ul className="mt-4 space-y-2 text-sm text-[var(--st-fg-muted)]">
            <Step done={phase !== "checking" && phase !== "idle"} active={phase === "checking"} label="Verify detection data" />
            <Step
              done={phase === "downloading" || phase === "done"}
              active={phase === "generating"}
              label="Generate PDF"
            />
            <Step done={phase === "done"} active={phase === "downloading"} label="Download PDF" />
          </ul>
        </div>
      ) : null}

      {error ? (
        <div
          role="alert"
          className="mx-6 mb-6 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-100"
        >
          {error}
        </div>
      ) : null}

      {noDetections && !detectionsLoading ? (
        <div className="mx-6 mb-6 rounded-lg border border-dashed border-[var(--st-border)] bg-[var(--st-muted)]/30 px-4 py-5 text-center">
          <Radar className="mx-auto h-8 w-8 text-[var(--st-fg-muted)]" aria-hidden />
          <p className="mt-3 text-sm text-[var(--st-fg-muted)]">
            No AI detection events yet. Reports need Microsoft 365 telemetry and at least one detection run.
          </p>
          <div className="mt-4 flex flex-wrap justify-center gap-2">
            <Link
              href="/dashboard/integrations"
              className="inline-flex h-9 items-center rounded-lg border border-[var(--st-border)] bg-[var(--st-surface)] px-4 text-sm font-medium hover:bg-[var(--st-muted)]"
            >
              Connect M365
            </Link>
            <Link
              href="/dashboard/detections"
              className="inline-flex h-9 items-center rounded-lg bg-[var(--st-accent)] px-4 text-sm font-medium text-white hover:opacity-90"
            >
              View AI events
            </Link>
          </div>
        </div>
      ) : null}

      {detectionsUnknown && !detectionsLoading ? null : null}
    </section>
  );
}

function Step({
  label,
  done,
  active,
}: {
  label: string;
  done: boolean;
  active: boolean;
}) {
  return (
    <li className={cn("flex items-center gap-2", (done || active) && "text-[var(--st-fg)]")}>
      <span
        className={cn(
          "flex h-5 w-5 items-center justify-center rounded-full border text-[10px] font-bold",
          done
            ? "border-emerald-500/50 bg-emerald-500/20 text-emerald-300"
            : active
              ? "border-[var(--st-accent)] bg-[var(--st-accent)]/20 text-[var(--st-accent)]"
              : "border-[var(--st-border)]",
        )}
        aria-hidden
      >
        {done ? "✓" : active ? "…" : ""}
      </span>
      {label}
    </li>
  );
}
