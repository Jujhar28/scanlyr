import { apiFetch } from "@/lib/api/client";

/** Backend `GET /detections` max page size (see `detections.py`). */
export const DETECTIONS_PAGE_LIMIT = 100;

export type RiskScore = {
  id: string;
  score_kind: string;
  score: string;
};

export type DetectionItem = {
  id: string;
  scan_session_id?: string | null;
  occurred_at: string;
  source: string;
  tool_name: string | null;
  tool_vendor?: string | null;
  channel: string | null;
  severity: string;
  confidence?: number | null;
  external_ref?: string | null;
  evidence?: Record<string, unknown> | null;
  risk_scores: RiskScore[];
};

export type DetectionListResponse = {
  items: DetectionItem[];
  total: number;
  limit: number;
  offset: number;
};

export type FetchAllDetectionsResult = {
  items: DetectionItem[];
  total: number;
  /** True when more rows exist in the API than were fetched (hit `maxItems`). */
  truncated: boolean;
};

export type FetchAllDetectionsOptions = {
  /** Stop after this many items (default 500). Each request uses `limit` ≤ 100. */
  maxItems?: number;
};

/**
 * Fetch detection events using sequential pages of at most {@link DETECTIONS_PAGE_LIMIT}.
 */
export async function fetchAllDetections(
  options: FetchAllDetectionsOptions = {},
): Promise<FetchAllDetectionsResult> {
  const maxItems = options.maxItems ?? 500;
  const items: DetectionItem[] = [];
  let offset = 0;
  let total = 0;

  while (items.length < maxItems) {
    const pageSize = Math.min(DETECTIONS_PAGE_LIMIT, maxItems - items.length);
    const page = await apiFetch<DetectionListResponse>(
      `detections?limit=${pageSize}&offset=${offset}`,
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
    items,
    total,
    truncated: total > items.length,
  };
}

export type DetectionRunResponse = {
  scan_session_id: string;
  events_normalized: number;
  candidates: number;
  inserted: number;
  skipped_duplicates: number;
};

export async function runDetectionScan(top = 120): Promise<DetectionRunResponse> {
  return apiFetch<DetectionRunResponse>(`detections/run?top=${top}`, { method: "POST" });
}
