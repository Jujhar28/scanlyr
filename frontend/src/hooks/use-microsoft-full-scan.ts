"use client";

import { useCallback, useState } from "react";

import { ApiError } from "@/lib/api/client";
import { runMicrosoftFullScan, type ScanPipelineResponse } from "@/lib/api/full-scan";
import { syncMicrosoft365 } from "@/lib/api/microsoft-integration";

export type FullScanPhase =
  | "idle"
  | "syncing"
  | "scanning"
  | "done"
  | "error";

const PHASE_PROGRESS: Record<FullScanPhase, number> = {
  idle: 0,
  syncing: 28,
  scanning: 72,
  done: 100,
  error: 0,
};

export type UseMicrosoftFullScanOptions = {
  /** Skip Graph ingestion sync (not recommended for first run). */
  skipSync?: boolean;
  graphTop?: number;
};

export function useMicrosoftFullScan() {
  const [phase, setPhase] = useState<FullScanPhase>("idle");
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ScanPipelineResponse | null>(null);

  const reset = useCallback(() => {
    setPhase("idle");
    setError(null);
    setResult(null);
  }, []);

  const run = useCallback(
    async (options: UseMicrosoftFullScanOptions = {}) => {
      const { skipSync = false, graphTop = 120 } = options;
      setError(null);
      setResult(null);

      try {
        if (!skipSync) {
          setPhase("syncing");
          await syncMicrosoft365();
        }

        setPhase("scanning");
        const pipeline = await runMicrosoftFullScan(graphTop);
        setResult(pipeline);
        setPhase("done");
        return pipeline;
      } catch (e) {
        const message =
          e instanceof ApiError
            ? e.message
            : e instanceof Error
              ? e.message
              : "Full scan failed.";
        setError(message);
        setPhase("error");
        throw e;
      }
    },
    [],
  );

  const isRunning = phase === "syncing" || phase === "scanning";
  const progress = PHASE_PROGRESS[phase];

  return {
    phase,
    progress,
    error,
    result,
    isRunning,
    run,
    reset,
  };
}
