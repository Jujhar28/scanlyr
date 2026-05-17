import type { DetectionItem } from "@/lib/api/detections";
import type { ScanHistorySummary } from "@/lib/api/scan-history";

import type { OverviewActivityItem } from "./types";

function detectionScore(row: DetectionItem): number | null {
  const r = row.risk_scores.find((s) => s.score_kind === "detection");
  return r ? Number(r.score) : null;
}

export function buildRecentActivity(
  scans: ScanHistorySummary[],
  detections: DetectionItem[],
  limit = 10,
): OverviewActivityItem[] {
  const scanItems: OverviewActivityItem[] = scans.map((s) => ({
    id: `scan-${s.id}`,
    kind: "paste_scan",
    occurredAt: s.scanned_at,
    title: "Security scan",
    subtitle: s.input_preview || `${s.content_type} · ${s.finding_count} findings`,
    severity: s.risk_level,
    riskScore: s.risk_score,
    href: `/dashboard/history/${s.id}`,
  }));

  const detectionItems: OverviewActivityItem[] = detections.map((d) => ({
    id: `det-${d.id}`,
    kind: "ai_event",
    occurredAt: d.occurred_at,
    title: d.tool_name ?? "Unknown AI tool",
    subtitle: d.channel ?? d.source,
    severity: d.severity,
    riskScore: detectionScore(d),
    href: `/dashboard/detections/${d.id}`,
  }));

  return [...scanItems, ...detectionItems]
    .sort((a, b) => new Date(b.occurredAt).getTime() - new Date(a.occurredAt).getTime())
    .slice(0, limit);
}

export function countHighRiskDetections(items: DetectionItem[]): number {
  return items.filter((d) => d.severity === "high" || d.severity === "critical").length;
}
