import type { ScanPipelineResponse } from "@/lib/api/full-scan";

export const FULL_SCAN_SUCCESS_KEY = "scanlyr:full_scan_success";

export type StoredFullScanSuccess = {
  inserted: number;
  reportTitle: string;
  reportId: string;
  completedAt: string;
};

export function storeFullScanSuccess(result: ScanPipelineResponse): void {
  if (typeof sessionStorage === "undefined") return;
  const payload: StoredFullScanSuccess = {
    inserted: result.detection_events_inserted,
    reportTitle: result.report.title,
    reportId: result.report.id,
    completedAt: new Date().toISOString(),
  };
  sessionStorage.setItem(FULL_SCAN_SUCCESS_KEY, JSON.stringify(payload));
}

export function consumeFullScanSuccess(): StoredFullScanSuccess | null {
  if (typeof sessionStorage === "undefined") return null;
  const raw = sessionStorage.getItem(FULL_SCAN_SUCCESS_KEY);
  if (!raw) return null;
  sessionStorage.removeItem(FULL_SCAN_SUCCESS_KEY);
  try {
    return JSON.parse(raw) as StoredFullScanSuccess;
  } catch {
    return null;
  }
}
