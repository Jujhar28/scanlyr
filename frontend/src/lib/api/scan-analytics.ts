import { apiFetch } from "@/lib/api/client";

export type RiskLevelCount = {
  risk_level: string;
  count: number;
};

export type ScanTrendPoint = {
  date: string;
  scan_count: number;
  average_risk_score: number | null;
};

export type ScanAnalyticsResponse = {
  organization_id: string;
  total_scans: number;
  average_risk_score: number | null;
  risk_level_distribution: RiskLevelCount[];
  top_threats: { risk_category: string; count: number }[];
  trends: ScanTrendPoint[];
};

export async function fetchScanAnalytics(trendDays = 30): Promise<ScanAnalyticsResponse> {
  return apiFetch<ScanAnalyticsResponse>(`scan/analytics?trend_days=${trendDays}`);
}
