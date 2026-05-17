"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle, ChevronDown, ChevronUp, ShieldAlert } from "lucide-react";

import type { ScanFinding } from "@/lib/api/scan";
import { RiskBadge } from "@/components/intel";
import { cn } from "@/lib/utils/cn";

export function FindingCard({
  finding,
  index = 0,
}: {
  finding: ScanFinding;
  index?: number;
}) {
  const [expanded, setExpanded] = useState(false);
  const Icon =
    finding.severity === "critical" || finding.severity === "high" ? ShieldAlert : AlertTriangle;
  const level =
    finding.severity === "critical" ||
    finding.severity === "high" ||
    finding.severity === "medium" ||
    finding.severity === "low"
      ? finding.severity
      : "medium";

  return (
    <motion.article
      initial={{ opacity: 0, y: 20, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ delay: index * 0.08, duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
      whileHover={{ y: -2 }}
      className="group overflow-hidden rounded-2xl border border-[var(--st-border)] bg-[var(--st-surface)] shadow-sm transition-shadow hover:shadow-[var(--st-shadow-lg)]"
    >
      <div className="absolute inset-y-0 left-0 w-1 bg-gradient-to-b from-[var(--st-accent)] to-[var(--st-accent-secondary)] opacity-0 transition group-hover:opacity-100" />
      <div className="p-4">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
          className="flex gap-3"
        >
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
            className={cn(
              "flex h-10 w-10 shrink-0 items-center justify-center rounded-xl",
              level === "high" || level === "critical"
                ? "bg-rose-50 text-rose-600"
                : level === "medium"
                  ? "bg-amber-50 text-amber-700"
                  : "bg-emerald-50 text-emerald-700",
            )}
          >
            <Icon className="h-5 w-5" aria-hidden />
          </motion.div>
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-start justify-between gap-2">
              <h3 className="font-display text-sm font-semibold text-[var(--st-fg)]">{finding.title}</h3>
              <RiskBadge level={level} />
            </div>
            <p className="mt-2 text-sm leading-relaxed text-[var(--st-fg-muted)]">{finding.description}</p>
            <div className="mt-3 rounded-lg border border-emerald-500/20 bg-emerald-50/60 px-3 py-2 text-xs text-emerald-900">
              <span className="font-semibold">Recommended action · </span>
              {finding.remediation}
            </div>
            {(finding.evidence && Object.keys(finding.evidence).length > 0) || finding.category ? (
              <button
                type="button"
                onClick={() => setExpanded((v) => !v)}
                className="mt-3 flex items-center gap-1 text-xs font-semibold text-[var(--st-accent)] hover:underline"
              >
                {expanded ? "Hide evidence" : "View evidence"}
                {expanded ? (
                  <ChevronUp className="h-3.5 w-3.5" aria-hidden />
                ) : (
                  <ChevronDown className="h-3.5 w-3.5" aria-hidden />
                )}
              </button>
            ) : null}
            <AnimatePresence>
              {expanded ? (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="overflow-hidden"
                >
                  <pre className="mt-2 max-h-32 overflow-auto rounded-lg bg-[var(--st-muted)] p-2 font-mono text-[10px] text-[var(--st-fg-muted)]">
                    {finding.evidence
                      ? JSON.stringify(finding.evidence, null, 2)
                      : finding.category}
                  </pre>
                </motion.div>
              ) : null}
            </AnimatePresence>
          </div>
        </motion.div>
      </div>
    </motion.article>
  );
}
