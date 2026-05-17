import { apiFetch, apiFetchBlob } from "@/lib/api/client";

export type ReportSummary = {
  id: string;
  title: string;
  report_type: string;
  status: string;
  period_start: string | null;
  period_end: string | null;
  created_at: string;
  downloadable: boolean;
};

export type ReportListResponse = {
  items: ReportSummary[];
  total: number;
  limit: number;
  offset: number;
};

export type ReportDetail = {
  id: string;
  title: string;
  report_type: string;
  status: string;
  period_start: string | null;
  period_end: string | null;
  created_at: string;
  updated_at: string;
  created_by_user_id: string | null;
  error_message: string | null;
  downloadable: boolean;
  meta: {
    sections?: Record<string, unknown>;
    version?: number;
    algorithm?: string;
  } | null;
};

export type GenerateReportRequest = {
  period_start?: string;
  period_end?: string;
};

export type GenerateReportResponse = {
  id: string;
  title: string;
  status: string;
};

export async function listReports(limit = 50, offset = 0): Promise<ReportListResponse> {
  return apiFetch<ReportListResponse>(`reports?limit=${limit}&offset=${offset}`);
}

export async function getReport(reportId: string): Promise<ReportDetail> {
  return apiFetch<ReportDetail>(`reports/${reportId}`);
}

export async function generateReport(
  body: GenerateReportRequest = {},
): Promise<GenerateReportResponse> {
  return apiFetch<GenerateReportResponse>("reports/generate", {
    method: "POST",
    json: body,
  });
}

export async function downloadReportPdf(reportId: string, filename?: string): Promise<void> {
  const blob = await apiFetchBlob(`reports/${reportId}/download`);
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename ?? `scanlyr-report-${reportId}.pdf`;
  a.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}
