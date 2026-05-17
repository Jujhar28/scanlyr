import { apiFetch } from "@/lib/api/client";
import type { ContentType, ScanFinding, ScanResponse } from "@/lib/api/scan";

/** Backend `GET /scan/history` max page size. */
export const SCAN_HISTORY_PAGE_LIMIT = 100;

export type RiskLevel = "low" | "medium" | "high" | "critical";

export type ScanHistorySummary = {
  id: string;
  scanned_at: string;
  user_id: string | null;
  content_type: ContentType;
  risk_score: number;
  risk_level: RiskLevel;
  confidence: number;
  finding_count: number;
  input_text: string | null;
  input_preview: string;
  engine_version: string;
};

export type ScanHistoryDetail = ScanHistorySummary & {
  findings: ScanFinding[];
  result: ScanResponse;
  detection_event_id: string | null;
};

export type ScanHistoryListResponse = {
  items: ScanHistorySummary[];
  total: number;
  limit: number;
  offset: number;
};

export type FetchAllScanHistoryResult = {
  items: ScanHistorySummary[];
  total: number;
  truncated: boolean;
};

export type FetchAllScanHistoryOptions = {
  maxItems?: number;
};

export async function fetchScanHistoryDetail(scanId: string): Promise<ScanHistoryDetail> {
  return apiFetch<ScanHistoryDetail>(`scan/history/${scanId}`);
}

/**
 * Fetch paste scan history using sequential pages (newest first per API ordering).
 */
export async function fetchAllScanHistory(
  options: FetchAllScanHistoryOptions = {},
): Promise<FetchAllScanHistoryResult> {
  const maxItems = options.maxItems ?? 200;
  const items: ScanHistorySummary[] = [];
  let offset = 0;
  let total = 0;

  while (items.length < maxItems) {
    const pageSize = Math.min(SCAN_HISTORY_PAGE_LIMIT, maxItems - items.length);
    const page = await apiFetch<ScanHistoryListResponse>(
      `scan/history?limit=${pageSize}&offset=${offset}`,
    );
    total = page.total;
    if (page.items.length === 0) {
      break;
    }
    items.push(...page.items);
    offset += page.items.length;
    if (items.length >= total) {
      break;
    }
  }

  return {
    items: sortScanHistoryNewestFirst(items),
    total,
    truncated: total > items.length,
  };
}

export function sortScanHistoryNewestFirst(rows: ScanHistorySummary[]): ScanHistorySummary[] {
  return [...rows].sort(
    (a, b) => new Date(b.scanned_at).getTime() - new Date(a.scanned_at).getTime(),
  );
}
