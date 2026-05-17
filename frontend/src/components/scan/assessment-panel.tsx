"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, Lightbulb } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

import type { ScanExplainability } from "@/lib/api/scan";
import { RiskBadge } from "@/components/intel";

type Props = {
  explainability: ScanExplainability;
};

export function AssessmentPanel({ explainability }: Props) {
  const [showBreakdown, setShowBreakdown] = useState(false);
  const [showTechnical, setShowTechnical] = useState(false);
  const { summary, rules, ai, composition, technical } = explainability;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, delay: 0.15 }}
      className="space-y-5"
    >
      <div>
        <h2 className="font-display text-xl font-bold tracking-tight text-[var(--st-fg)]">
          {summary.headline}
        </h2>
        <p className="mt-2 text-sm leading-relaxed text-[var(--st-fg-muted)]">{summary.summary}</p>
      </div>

      <div className="rounded-xl border border-[var(--st-accent)]/20 bg-gradient-to-r from-cyan-50/80 to-indigo-50/50 p-4">
        <div className="flex items-start gap-3">
          <Lightbulb className="mt-0.5 h-5 w-5 shrink-0 text-[var(--st-accent)]" aria-hidden />
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-[var(--st-accent-secondary)]">
              What to do next
            </p>
            <p className="mt-1 text-sm text-[var(--st-fg)]">
              {composition.method === "hybrid" && summary.risk_level === "low"
                ? "Treat as informational. Use real-secret handling only for production credentials."
                : composition.label}
            </p>
          </div>
        </div>
      </div>

      <button
        type="button"
        onClick={() => setShowBreakdown((v) => !v)}
        className="flex w-full items-center justify-between rounded-xl border border-[var(--st-border)] bg-[var(--st-muted)]/50 px-4 py-3 text-left text-sm font-semibold text-[var(--st-fg)] transition hover:border-[var(--st-accent)]/30"
      >
        How we assessed this
        {showBreakdown ? (
          <ChevronUp className="h-4 w-4 text-[var(--st-fg-muted)]" aria-hidden />
        ) : (
          <ChevronDown className="h-4 w-4 text-[var(--st-fg-muted)]" aria-hidden />
        )}
      </button>

      <AnimatePresence>
        {showBreakdown ? (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="grid gap-3 sm:grid-cols-2">
              <LayerCard title="Pattern analysis" score={rules.score} level={rules.risk_level}>
                <p className="text-sm leading-relaxed text-[var(--st-fg-muted)]">{rules.summary}</p>
                {rules.primary_concerns.length > 0 ? (
                  <ul className="mt-3 space-y-1">
                    {rules.primary_concerns.map((c) => (
                      <li
                        key={c}
                        className="flex items-start gap-2 text-sm text-[var(--st-fg)] before:mt-2 before:h-1 before:w-1 before:shrink-0 before:rounded-full before:bg-[var(--st-accent)] before:content-['']"
                      >
                        {c}
                      </li>
                    ))}
                  </ul>
                ) : null}
              </LayerCard>

              {ai.used ? (
                <LayerCard title="Contextual review" score={ai.score ?? 0} level={ai.risk_level ?? "low"}>
                  {ai.category ? (
                    <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--st-accent-secondary)]">
                      {ai.category.replace(/_/g, " ")}
                    </p>
                  ) : null}
                  <p className="text-sm leading-relaxed text-[var(--st-fg-muted)]">{ai.summary}</p>
                </LayerCard>
              ) : (
                <div className="rounded-xl border border-dashed border-[var(--st-border)] bg-white/60 px-4 py-4">
                  <p className="text-xs font-semibold uppercase tracking-wide text-[var(--st-fg-muted)]">
                    Contextual review
                  </p>
                  <p className="mt-1 text-sm text-[var(--st-fg-muted)]">
                    Pattern analysis alone determined this score.
                  </p>
                </div>
              )}
            </div>

            <p className="mt-3 text-center text-xs text-[var(--st-fg-muted)]">
              Overall risk: <strong className="text-[var(--st-fg)]">{composition.combined_score}</strong> / 100
            </p>
          </motion.div>
        ) : null}
      </AnimatePresence>

      {technical ? (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
        >
          <button
            type="button"
            onClick={() => setShowTechnical((v) => !v)}
            className="flex w-full items-center justify-between rounded-xl border border-[var(--st-border)] px-3 py-2 text-left text-xs font-medium text-[var(--st-fg-muted)] hover:bg-[var(--st-muted)]"
          >
            Advanced details (optional)
            {showTechnical ? (
              <ChevronUp className="h-4 w-4" aria-hidden />
            ) : (
              <ChevronDown className="h-4 w-4" aria-hidden />
            )}
          </button>
          <AnimatePresence>
            {showTechnical ? (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="mt-2 space-y-2 rounded-xl border border-[var(--st-border)] bg-[var(--st-muted)]/40 p-3 text-xs text-[var(--st-fg-muted)]"
              >
                {technical.engine_version ? <p>Engine {technical.engine_version}</p> : null}
                {technical.rules_engine_detail ? (
                  <p className="whitespace-pre-wrap leading-relaxed">{technical.rules_engine_detail}</p>
                ) : null}
                {technical.ai_detail ? (
                  <p className="whitespace-pre-wrap leading-relaxed">{technical.ai_detail}</p>
                ) : null}
              </motion.div>
            ) : null}
          </AnimatePresence>
        </motion.div>
      ) : null}
    </motion.div>
  );
}

function LayerCard({
  title,
  score,
  level,
  children,
}: {
  title: string;
  score: number;
  level: string;
  children: React.ReactNode;
}) {
  const riskLevel =
    level === "low" || level === "medium" || level === "high" || level === "critical"
      ? level
      : "low";

  return (
    <div className="rounded-xl border border-[var(--st-border)] bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between gap-2">
        <p className="text-xs font-semibold uppercase tracking-wide text-[var(--st-fg-muted)]">{title}</p>
        <div className="flex items-center gap-2">
          <RiskBadge level={riskLevel} />
          <span className="font-display text-lg font-bold tabular-nums text-[var(--st-fg)]">{score}</span>
        </div>
      </div>
      {children}
    </div>
  );
}
