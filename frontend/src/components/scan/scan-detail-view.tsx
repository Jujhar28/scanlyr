"use client";

import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { motion } from "framer-motion";

import {
  AnimatedRiskGauge,
  IntelCard,
  PageHero,
  StaggerItem,
  StaggerReveal,
} from "@/components/intel";
import { AssessmentPanel } from "@/components/scan/assessment-panel";
import { FindingCard } from "@/components/scan/finding-card";
import { CategoryBreakdown } from "@/components/scan/category-breakdown";
import type { ScanHistoryDetail } from "@/lib/api/scan-history";
import { scanAnalysis, scanExplainability } from "@/lib/api/scan";

export function ScanDetailView({ detail }: { detail: ScanHistoryDetail }) {
  const result = detail.result;
  const explainability = scanExplainability(result);

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      className="mx-auto max-w-[1680px] space-y-6 pb-10"
    >
      <Link
        href="/dashboard/history"
        className="inline-flex items-center gap-1 text-sm font-semibold text-[var(--st-accent)] hover:underline"
      >
        <ArrowLeft className="h-4 w-4" aria-hidden />
        Back to history
      </Link>

      <PageHero
        eyebrow="Scan assessment"
        title="Intelligence report"
        description={`Scanned ${new Date(detail.scanned_at).toLocaleString()} · ${detail.content_type} mode`}
      />

      <StaggerReveal className="space-y-6">
        <StaggerItem>
          <IntelCard accent="cyan" noPadding>
            <div className="grid gap-6 p-6 lg:grid-cols-[auto_1fr]">
              <AnimatedRiskGauge
                score={result.risk_score}
                level={result.risk_level}
                confidence={result.confidence}
                animateKey={detail.id}
              />
              <div className="space-y-4">
                {explainability ? (
                  <AssessmentPanel explainability={explainability} />
                ) : (
                  <p className="text-sm text-[var(--st-fg-muted)]">{result.explanation}</p>
                )}
                <div className="rounded-xl border border-[var(--st-border)] bg-[var(--st-muted)]/50 p-4">
                  <p className="text-xs font-semibold uppercase tracking-wide text-[var(--st-fg-muted)]">
                    Scanned content
                  </p>
                  <p className="mt-2 font-mono text-xs leading-relaxed text-[var(--st-fg)]">
                    {detail.input_text ?? detail.input_preview}
                  </p>
                </div>
              </div>
            </div>
          </IntelCard>
        </StaggerItem>

        <div className="grid gap-4 md:grid-cols-2">
          <StaggerItem>
            <IntelCard title="Risk categories" accent="amber">
              <CategoryBreakdown
                categories={scanAnalysis(result)?.score_breakdown.categories ?? []}
              />
            </IntelCard>
          </StaggerItem>
          <StaggerItem>
            <IntelCard title="Recommended actions" accent="neon">
              {result.remediation.length ? (
                <ol className="list-decimal space-y-2 pl-4 text-sm text-[var(--st-fg)]">
                  {result.remediation.map((r) => (
                    <li key={r}>{r}</li>
                  ))}
                </ol>
              ) : (
                <p className="text-sm text-[var(--st-fg-muted)]">No remediations required.</p>
              )}
            </IntelCard>
          </StaggerItem>
        </div>

        <StaggerItem>
          <h3 className="mb-4 font-display text-lg font-bold text-[var(--st-fg)]">
            Evidence ({detail.findings.length})
          </h3>
          <div className="grid gap-3 sm:grid-cols-2">
            {detail.findings.map((f, i) => (
              <FindingCard key={`${f.title}-${i}`} finding={f} index={i} />
            ))}
          </div>
        </StaggerItem>
      </StaggerReveal>
    </motion.div>
  );
}
