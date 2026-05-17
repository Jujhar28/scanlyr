"use client";

import { useCallback, useEffect, useState } from "react";

import { apiFetch, ApiError } from "@/lib/api/client";
import { fetchAllDetections } from "@/lib/api/detections";
import { fetchScanAnalytics } from "@/lib/api/scan-analytics";
import { fetchAllScanHistory } from "@/lib/api/scan-history";
import { buildRecentActivity, countHighRiskDetections } from "@/lib/overview/activity";
import type { OverviewActivityItem, OverviewSnapshot } from "@/lib/overview/types";

type MicrosoftGraphStatus = {
  status: string;
  last_sync_at: string | null;
  connected_at: string | null;
  last_error_message: string | null;
};

export type UseOverviewDataResult = OverviewSnapshot & {
  activity: OverviewActivityItem[];
  loading: boolean;
  warnings: string[];
  fatalError: string | null;
  reload: () => void;
};

export function useOverviewData(hydrated: boolean): UseOverviewDataResult {
  const [loading, setLoading] = useState(true);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [fatalError, setFatalError] = useState<string | null>(null);
  const [snapshot, setSnapshot] = useState<OverviewSnapshot>({
    msft: null,
    analytics: null,
    lastScan: null,
    detections: null,
  });
  const [activity, setActivity] = useState<OverviewActivityItem[]>([]);

  const load = useCallback(async () => {
    setLoading(true);
    setFatalError(null);
    const nextWarnings: string[] = [];

    const [msftResult, analyticsResult, scanHistoryResult, detectionsResult] =
      await Promise.allSettled([
        apiFetch<MicrosoftGraphStatus>("integrations/microsoft/status"),
        fetchScanAnalytics(30),
        fetchAllScanHistory({ maxItems: 15 }),
        fetchAllDetections({ maxItems: 100 }),
      ]);

    let msft: OverviewSnapshot["msft"] = null;
    let analytics: OverviewSnapshot["analytics"] = null;
    let lastScan: OverviewSnapshot["lastScan"] = null;
    let detections: OverviewSnapshot["detections"] = null;

    if (msftResult.status === "fulfilled") {
      msft = {
        status: msftResult.value.status,
        last_sync_at: msftResult.value.last_sync_at,
        connected_at: msftResult.value.connected_at,
        last_error_message: msftResult.value.last_error_message,
      };
    } else {
      nextWarnings.push(
        msftResult.reason instanceof ApiError
          ? msftResult.reason.message
          : "Could not load Microsoft 365 status.",
      );
    }

    if (analyticsResult.status === "fulfilled") {
      analytics = analyticsResult.value;
    } else {
      nextWarnings.push(
        analyticsResult.reason instanceof ApiError
          ? analyticsResult.reason.message
          : "Could not load scan analytics.",
      );
    }

    if (scanHistoryResult.status === "fulfilled") {
      lastScan = scanHistoryResult.value.items[0] ?? null;
    } else {
      nextWarnings.push(
        scanHistoryResult.reason instanceof ApiError
          ? scanHistoryResult.reason.message
          : "Could not load scan history.",
      );
    }

    if (detectionsResult.status === "fulfilled") {
      const d = detectionsResult.value;
      detections = {
        items: d.items,
        total: d.total,
        highRiskCount: countHighRiskDetections(d.items),
      };
      if (d.truncated) {
        nextWarnings.push("AI event counts use the most recent 100 records.");
      }
    } else {
      nextWarnings.push(
        detectionsResult.reason instanceof ApiError
          ? detectionsResult.reason.message
          : "Could not load AI events.",
      );
    }

    const scanItems = scanHistoryResult.status === "fulfilled" ? scanHistoryResult.value.items : [];
    const detectionItems =
      detectionsResult.status === "fulfilled" ? detectionsResult.value.items : [];

    setSnapshot({ msft, analytics, lastScan, detections });
    setActivity(buildRecentActivity(scanItems, detectionItems));
    setWarnings(nextWarnings);

    const allFailed =
      msftResult.status === "rejected" &&
      analyticsResult.status === "rejected" &&
      detectionsResult.status === "rejected";
    setFatalError(allFailed ? "Could not load overview data. Check the API and your session." : null);
    setLoading(false);
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    void load();
  }, [hydrated, load]);

  return {
    ...snapshot,
    activity,
    loading,
    warnings,
    fatalError,
    reload: load,
  };
}
