export { apiFetch, apiFetchBlob, ApiError } from "./client";
export {
  DETECTIONS_PAGE_LIMIT,
  fetchAllDetections,
  runDetectionScan,
  type DetectionItem,
  type DetectionListResponse,
  type FetchAllDetectionsResult,
} from "./detections";
export { runMicrosoftFullScan, type ScanPipelineResponse } from "./full-scan";
export { syncMicrosoft365, type MicrosoftGraphSyncResponse } from "./microsoft-integration";
export { fetchScanAnalytics, type ScanAnalyticsResponse } from "./scan-analytics";
export {
  downloadReportPdf,
  generateReport,
  getReport,
  listReports,
  type GenerateReportResponse,
  type ReportDetail,
  type ReportSummary,
} from "./reports";
export {
  SCAN_HISTORY_PAGE_LIMIT,
  fetchAllScanHistory,
  sortScanHistoryNewestFirst,
  type ScanHistorySummary,
  type ScanHistoryListResponse,
  type FetchAllScanHistoryResult,
} from "./scan-history";
export type { ApiClientOptions } from "./client";
export type { ApiErrorBody, HttpMethod } from "./types";
