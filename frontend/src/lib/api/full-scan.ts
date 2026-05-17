import { apiFetch } from "@/lib/api/client";

export type ScanPipelineReportRef = {
  id: string;
  status: string;
  title: string;
  downloadable: boolean;
};

export type ScanPipelineResponse = {
  mode: string;
  scan_session_id: string;
  detection_events_inserted: number;
  risk_scores_created: number;
  report: ScanPipelineReportRef;
};

/**
 * End-to-end Microsoft Graph scan: detection rules → risk scores → compliance report.
 * Uses `POST /detections/pipeline` with `mode: microsoft_graph`.
 */
export async function runMicrosoftFullScan(graphTop = 120): Promise<ScanPipelineResponse> {
  return apiFetch<ScanPipelineResponse>("detections/pipeline", {
    method: "POST",
    json: { mode: "microsoft_graph", graph_top: graphTop },
  });
}
