import { apiFetch } from "@/lib/api/client";

export type ContentType = "prompt" | "output" | "auto";

export type ScanFinding = {
  type: string;
  detector: string;
  category: string;
  risk_category: string;
  severity: "low" | "medium" | "high" | "critical";
  title: string;
  description: string;
  confidence: number;
  remediation: string;
  evidence?: Record<string, unknown> | null;
};

export type CategoryScore = {
  risk_category: string;
  score: number;
  finding_count: number;
  explanation: string;
};

export type ScoreBreakdown = {
  overall: number;
  categories: CategoryScore[];
  top_drivers: string[];
};

export type ScanMetadata = {
  scan_id: string;
  timestamp: string;
  request_id?: string | null;
  content_type: ContentType;
  engine_version: string;
  schema_version: string;
};

export type ScanAssessmentSummary = {
  headline: string;
  score: number;
  risk_level: "low" | "medium" | "high" | "critical";
  summary: string;
};

export type ScanRulesAssessment = {
  score: number;
  risk_level: "low" | "medium" | "high" | "critical";
  summary: string;
  primary_concerns: string[];
  top_categories: string[];
};

export type ScanAIAssessment = {
  used: boolean;
  score?: number | null;
  risk_level?: "low" | "medium" | "high" | "critical" | null;
  category?: string | null;
  summary?: string | null;
};

export type ScanComposition = {
  method: "hybrid" | "rules_only" | "safe_default";
  combined_score: number;
  label: string;
  rules_weight_percent: number;
  ai_weight_percent?: number | null;
  rules_score: number;
  ai_score?: number | null;
};

export type ScanTechnicalDetails = {
  engine_version?: string | null;
  rules_engine_detail?: string | null;
  ai_provider?: string | null;
  ai_fallback_used?: boolean;
  ai_detail?: string | null;
  fusion_weights?: Record<string, number> | null;
};

export type ScanExplainability = {
  summary: ScanAssessmentSummary;
  rules: ScanRulesAssessment;
  ai: ScanAIAssessment;
  composition: ScanComposition;
  technical?: ScanTechnicalDetails | null;
};

export type ScanAnalysis = {
  risk_categories: Record<string, number>;
  score_breakdown: ScoreBreakdown;
  explainability?: ScanExplainability | null;
};

export type ScanResponse = {
  risk_score: number;
  risk_level: "low" | "medium" | "high" | "critical";
  confidence: number;
  explanation: string;
  findings: ScanFinding[];
  remediation: string[];
  metadata: ScanMetadata;
  analysis?: ScanAnalysis | null;
};

/** Resolve explainability block (supports legacy payloads without `analysis`). */
export function scanAnalysis(res: ScanResponse): ScanAnalysis | null {
  if (res.analysis) return res.analysis;
  const legacy = res as ScanResponse & {
    score_breakdown?: ScoreBreakdown;
    risk_categories?: Record<string, number>;
  };
  if (legacy.score_breakdown) {
    return {
      risk_categories: legacy.risk_categories ?? {},
      score_breakdown: legacy.score_breakdown,
    };
  }
  return null;
}

/** Structured assessment layers (v2.1+), or null for legacy scans. */
export function scanExplainability(res: ScanResponse): ScanExplainability | null {
  return scanAnalysis(res)?.explainability ?? null;
}

export async function runSecurityScan(input_text: string, content_type: ContentType = "auto") {
  return apiFetch<ScanResponse>("scan", {
    method: "POST",
    json: { input_text, content_type },
  });
}
