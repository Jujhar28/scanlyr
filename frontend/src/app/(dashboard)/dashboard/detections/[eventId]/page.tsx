"use client";

import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { ButtonLink } from "@/components/ui/button";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { PageHeader } from "@/components/dashboard/page-header";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { apiFetch, ApiError } from "@/lib/api/client";
import { useAuth } from "@/providers/auth-provider";

type RiskScore = {
  id: string;
  score_kind: string;
  score: string;
  factors: Record<string, unknown> | null;
  algorithm_version: string;
  computed_at: string;
};

type DetectionDetail = {
  id: string;
  scan_session_id: string | null;
  occurred_at: string;
  source: string;
  tool_name: string | null;
  tool_vendor: string | null;
  channel: string | null;
  severity: string;
  confidence: number | null;
  external_ref: string | null;
  evidence: Record<string, unknown> | null;
  risk_scores: RiskScore[];
};

export default function DetectionDetailPage() {
  const params = useParams();
  const id = typeof params.eventId === "string" ? params.eventId : "";
  const { hydrated } = useAuth();
  const [row, setRow] = useState<DetectionDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const res = await apiFetch<DetectionDetail>(`detections/${id}`);
      setRow(res);
    } catch (e) {
      setRow(null);
      setError(e instanceof ApiError ? e.message : "Failed to load detection.");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    if (!hydrated || !id) return;
    void load();
  }, [hydrated, id, load]);

  if (!hydrated) {
    return null;
  }

  return (
    <div className="mx-auto max-w-[1600px] space-y-6">
      <div className="flex flex-wrap items-center gap-3">
        <ButtonLink href="/dashboard/detections" variant="ghost" className="h-9 px-3 text-sm">
          ← AI events
        </ButtonLink>
      </div>

      {loading ? (
        <div className="space-y-4">
          <Skeleton className="h-12 w-full max-w-lg rounded-lg" />
          <Skeleton className="h-40 rounded-xl" />
          <Skeleton className="h-48 rounded-xl" />
        </div>
      ) : null}

      {error ? (
        <p className="text-sm text-red-200" role="alert">
          {error}
        </p>
      ) : null}

      {row ? (
        <>
          <PageHeader
            title={row.tool_name ?? "Unknown tool"}
            description={`${row.tool_vendor ?? "Unknown vendor"} · ${new Date(row.occurred_at).toLocaleString()}`}
            actions={
              <Badge
                variant={
                  row.severity === "critical" || row.severity === "high"
                    ? "danger"
                    : row.severity === "medium"
                      ? "warning"
                      : "outline"
                }
              >
                {row.severity}
              </Badge>
            }
          />

          <Card className="border-[var(--st-border)] bg-[var(--st-surface)] shadow-sm">
            <CardHeader className="border-b border-[var(--st-border)] bg-[var(--st-muted)]/30">
              <CardTitle>Telemetry</CardTitle>
              <CardDescription>Source identifiers and confidence.</CardDescription>
            </CardHeader>
            <div className="space-y-4 p-6 text-sm">
              <dl className="grid gap-4 sm:grid-cols-2">
                <div>
                  <dt className="text-xs uppercase tracking-wider text-[var(--st-fg-muted)]">Source</dt>
                  <dd className="mt-1 font-medium text-[var(--st-fg)]">{row.source}</dd>
                </div>
                <div>
                  <dt className="text-xs uppercase tracking-wider text-[var(--st-fg-muted)]">Channel</dt>
                  <dd className="mt-1 text-[var(--st-fg)]">{row.channel ?? "—"}</dd>
                </div>
                <div>
                  <dt className="text-xs uppercase tracking-wider text-[var(--st-fg-muted)]">Confidence</dt>
                  <dd className="mt-1 tabular-nums text-[var(--st-fg)]">{row.confidence ?? "—"}</dd>
                </div>
                <div>
                  <dt className="text-xs uppercase tracking-wider text-[var(--st-fg-muted)]">External ref</dt>
                  <dd className="mt-1 break-all font-mono text-xs text-[var(--st-fg-muted)]">{row.external_ref ?? "—"}</dd>
                </div>
              </dl>
            </div>
          </Card>
          <Card className="border-[var(--st-border)] bg-[var(--st-surface)] shadow-sm">
            <CardHeader className="border-b border-[var(--st-border)] bg-[var(--st-muted)]/30">
              <CardTitle>Risk scores</CardTitle>
              <CardDescription>Detection-level and related scoring factors.</CardDescription>
            </CardHeader>
            <div className="space-y-3 p-6">
              {row.risk_scores.length === 0 ? (
                <p className="text-sm text-[var(--st-fg-muted)]">No scores attached.</p>
              ) : (
                <ul className="space-y-2">
                  {row.risk_scores.map((s) => (
                    <li
                      key={s.id}
                      className="rounded-lg border border-[var(--st-border)] bg-[var(--st-muted)]/30 p-3 text-sm"
                    >
                      <p className="font-medium text-[var(--st-fg)]">
                        {s.score_kind} · {s.score}
                      </p>
                      <p className="text-xs text-[var(--st-fg-muted)]">{s.algorithm_version}</p>
                      {s.factors ? (
                        <pre className="mt-2 max-h-48 overflow-auto rounded bg-black/30 p-2 text-xs text-[var(--st-fg-muted)]">
                          {JSON.stringify(s.factors, null, 2)}
                        </pre>
                      ) : null}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </Card>
          <Card className="border-[var(--st-border)] bg-[var(--st-surface)] shadow-sm">
            <CardHeader className="border-b border-[var(--st-border)] bg-[var(--st-muted)]/30">
              <CardTitle>Evidence</CardTitle>
              <CardDescription>Rule hits and raw snapshot (from Microsoft Graph).</CardDescription>
            </CardHeader>
            <div className="p-6">
              {row.evidence ? (
                <pre className="max-h-96 overflow-auto rounded-lg bg-black/30 p-3 text-xs text-[var(--st-fg-muted)]">
                  {JSON.stringify(row.evidence, null, 2)}
                </pre>
              ) : (
                <p className="text-sm text-[var(--st-fg-muted)]">No evidence payload.</p>
              )}
            </div>
          </Card>
        </>
      ) : null}
    </div>
  );
}
