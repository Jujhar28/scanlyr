"use client";

import Link from "next/link";
import { Loader2, Radar, ShieldCheck } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import type { FullScanPhase } from "@/hooks/use-microsoft-full-scan";
import { cn } from "@/lib/utils/cn";

function phaseLabel(phase: FullScanPhase): string {
  switch (phase) {
    case "syncing":
      return "Ingesting Microsoft 365 telemetry…";
    case "scanning":
      return "Running AI detection rules and building your report…";
    case "done":
      return "Full scan complete.";
    case "error":
      return "Full scan could not finish.";
    default:
      return "Ready to scan your tenant for shadow AI activity.";
  }
}

export function MicrosoftFullScanCard({
  connected,
  isAdmin,
  phase,
  progress,
  error,
  isRunning,
  onRun,
}: {
  connected: boolean;
  isAdmin: boolean;
  phase: FullScanPhase;
  progress: number;
  error: string | null;
  isRunning: boolean;
  onRun: () => void | Promise<void>;
}) {

  if (!connected) {
    return null;
  }

  return (
    <Card className="overflow-hidden border-[var(--st-accent)]/35 bg-gradient-to-br from-[var(--st-surface)] to-[var(--st-muted)]/50 shadow-md">
      <CardHeader className="border-b border-[var(--st-border)]/80 pb-4">
        <div className="flex items-start gap-3">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-[var(--st-accent)]/15 text-[var(--st-accent)]">
            <Radar className="h-6 w-6" aria-hidden />
          </div>
          <div>
            <CardTitle className="text-xl">Run Full Scan</CardTitle>
            <CardDescription className="mt-1">
              One workflow: sync Microsoft 365, detect shadow AI tools, score risk, and generate a
              compliance report.
            </CardDescription>
          </div>
        </div>
      </CardHeader>

      <div className="space-y-4 p-6">
        <p className="text-sm text-[var(--st-fg-muted)]">{phaseLabel(phase)}</p>

        {isRunning || phase === "done" ? (
          <Progress value={progress} className="h-2.5" />
        ) : null}

        {isRunning ? (
          <ul className="space-y-2 text-sm text-[var(--st-fg-muted)]">
            <li className={cn("flex items-center gap-2", phase === "syncing" && "text-[var(--st-fg)]")}>
              {phase === "syncing" ? (
                <Loader2 className="h-4 w-4 animate-spin text-[var(--st-accent)]" aria-hidden />
              ) : (
                <ShieldCheck className="h-4 w-4 text-emerald-400" aria-hidden />
              )}
              Sync telemetry
            </li>
            <li
              className={cn(
                "flex items-center gap-2",
                (phase === "scanning" || phase === "done") && "text-[var(--st-fg)]",
              )}
            >
              {phase === "scanning" ? (
                <Loader2 className="h-4 w-4 animate-spin text-[var(--st-accent)]" aria-hidden />
              ) : phase === "done" ? (
                <ShieldCheck className="h-4 w-4 text-emerald-400" aria-hidden />
              ) : (
                <span className="inline-block h-4 w-4 rounded-full border border-[var(--st-border)]" />
              )}
              Detect AI events &amp; generate report
            </li>
          </ul>
        ) : null}

        {error ? (
          <div
            role="alert"
            className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-100"
          >
            {error}
          </div>
        ) : null}

        {isAdmin ? (
          <div className="flex flex-wrap items-center gap-3 pt-1">
            <Button
              type="button"
              className="h-11 px-6 text-base font-semibold"
              disabled={isRunning}
              onClick={() => void onRun()}
            >
              {isRunning ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" aria-hidden />
                  Scanning…
                </>
              ) : (
                "Run Full Scan"
              )}
            </Button>
            <Link
              href="/dashboard/detections"
              className="text-sm font-medium text-[var(--st-accent)] hover:underline"
            >
              View AI events
            </Link>
          </div>
        ) : (
          <p className="text-sm text-[var(--st-fg-muted)]">
            Only organization administrators can run a full scan.
          </p>
        )}
      </div>
    </Card>
  );
}
