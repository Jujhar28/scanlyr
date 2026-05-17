import type { DetectionItem } from "@/lib/api/detections";
import type { ScanHistorySummary } from "@/lib/api/scan-history";
import type { ScanAnalyticsResponse } from "@/lib/api/scan-analytics";

export type MicrosoftOverviewStatus = {
  status: string;
  last_sync_at: string | null;
  connected_at: string | null;
  last_error_message: string | null;
};

export type OverviewSnapshot = {
  msft: MicrosoftOverviewStatus | null;
  analytics: ScanAnalyticsResponse | null;
  lastScan: ScanHistorySummary | null;
  detections: {
    items: DetectionItem[];
    total: number;
    highRiskCount: number;
  } | null;
};

export type ActivityKind = "paste_scan" | "ai_event";

export type OverviewActivityItem = {
  id: string;
  kind: ActivityKind;
  occurredAt: string;
  title: string;
  subtitle: string;
  severity?: string;
  riskScore?: number | null;
  href: string;
};
