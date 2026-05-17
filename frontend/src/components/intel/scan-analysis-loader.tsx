"use client";

import { motion } from "framer-motion";
import { Brain, Radar, Shield } from "lucide-react";

const steps = [
  { icon: Radar, label: "Parsing content signals" },
  { icon: Shield, label: "Running security patterns" },
  { icon: Brain, label: "Synthesizing risk assessment" },
];

export function ScanAnalysisLoader() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="relative flex min-h-[360px] flex-col items-center justify-center overflow-hidden rounded-2xl border border-[var(--st-accent)]/25 bg-gradient-to-b from-[var(--st-surface)] to-[var(--st-muted)] p-10"
    >
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div
          className="absolute inset-x-0 h-24 bg-gradient-to-b from-[var(--st-accent)]/20 to-transparent"
          style={{ animation: "st-scan-sweep 2.2s ease-in-out infinite" }}
        />
      </div>

      <motion.div
        className="relative flex h-20 w-20 items-center justify-center rounded-2xl border border-[var(--st-accent)]/30 bg-[var(--st-accent-subtle)]"
        animate={{ boxShadow: ["0 0 0 0 rgba(0,180,216,0.2)", "0 0 0 16px rgba(0,180,216,0)", "0 0 0 0 rgba(0,180,216,0)"] }}
        transition={{ duration: 2, repeat: Infinity }}
      >
        <Radar className="h-9 w-9 text-[var(--st-accent)]" aria-hidden />
      </motion.div>

      <p className="relative mt-6 font-display text-lg font-semibold text-[var(--st-fg)]">
        Intelligence engine analyzing…
      </p>
      <p className="relative mt-1 text-sm text-[var(--st-fg-muted)]">
        Correlating patterns and contextual risk
      </p>

      <ul className="relative mt-8 w-full max-w-xs space-y-3">
        {steps.map((step, i) => (
          <motion.li
            key={step.label}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.35, duration: 0.4 }}
            className="flex items-center gap-3 text-sm text-[var(--st-fg-muted)]"
          >
            <step.icon className="h-4 w-4 shrink-0 text-[var(--st-accent)]" aria-hidden />
            <span>{step.label}</span>
            <motion.span
              className="ml-auto h-1.5 w-1.5 rounded-full bg-[var(--st-accent)]"
              animate={{ opacity: [0.3, 1, 0.3] }}
              transition={{ duration: 1.2, repeat: Infinity, delay: i * 0.2 }}
            />
          </motion.li>
        ))}
      </ul>
    </motion.div>
  );
}
