"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  ArrowRight,
  Cloud,
  CloudOff,
  RefreshCw,
  ScanSearch,
  ShieldAlert,
  TrendingUp,
} from "lucide-react";

import { AnimatedRiskGauge, IntelCard, PageHero, RiskBadge, StaggerItem, StaggerReveal } from "@/components/intel";
import { Button } from "@/components/ui/button";
import { ButtonLink } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useOverviewData } from "@/hooks/use-overview-data";
import { useAuth } from "@/providers/auth-provider";
import { cn } from "@/lib/utils/cn";

export function OverviewDashboard() {
  const { hydrated } = useAuth();
  const {
    msft,
    analytics,
    lastScan,
    detections,
    activity,
    loading,
    warnings,
    fatalError,
    reload,
  } = useOverviewData(hydrated);

  if (!hydrated) return null;

  const connected = msft?.status === "connected";
  const recentHighRisk = activity.filter(
    (a) => a.severity === "high" || a.severity === "critical",
  ).slice(0, 3);

  return (
    <div className="mx-auto max-w-[1680px] space-y-6 pb-10">
      <PageHero
        eyebrow="Command center"
        title="Security intelligence"
        description="Live posture across paste scans, Microsoft 365 AI detection, and compliance reporting."
        actions={
          <>
            <Button
              type="button"
              variant="secondary"
              className="h-9 gap-2 px-3"
              disabled={loading}
              onClick={() => void reload()}
            >
              <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} aria-hidden />
              Refresh
            </Button>
            <ButtonLink href="/dashboard/scan" className="h-9 gap-2 px-4">
              <ScanSearch className="h-4 w-4" aria-hidden />
              Run scan
            </ButtonLink>
          </>
        }
      />

      {fatalError ? (
        <div
          role="alert"
          className="rounded-xl border border-rose-500/30 bg-rose-50 px-4 py-3 text-sm text-rose-800"
        >
          {fatalError}
        </div>
      ) : null}

      {warnings.length > 0 ? (
        <motion.div
          role="status"
          className="rounded-xl border border-amber-500/30 bg-amber-50 px-4 py-3 text-sm text-amber-900"
        >
          <ul className="list-inside list-disc space-y-1">
            {warnings.map((w) => (
              <li key={w}>{w}</li>
            ))}
          </ul>
        </motion.div>
      ) : null}

      <StaggerReveal className="grid auto-rows-min gap-4 lg:grid-cols-12">
        {/* Risk dial — hero bento */}
        <StaggerItem className="lg:col-span-4">
          <IntelCard title="Risk posture" description="Latest scan signal" accent="cyan" className="h-full">
            {loading ? (
              <Skeleton className="mx-auto h-40 w-40 rounded-full" />
            ) : lastScan ? (
              <div className="flex flex-col items-center py-2">
                <AnimatedRiskGauge
                  score={lastScan.risk_score}
                  level={lastScan.risk_level}
                  confidence={lastScan.confidence}
                  animateKey={lastScan.id}
                />
                <Link
                  href={`/dashboard/history/${lastScan.id}`}
                  className="mt-4 inline-flex items-center gap-1 text-sm font-semibold text-[var(--st-accent)] hover:underline"
                >
                  View assessment
                  <ArrowRight className="h-4 w-4" aria-hidden />
                </Link>
              </div>
            ) : (
              <div className="py-8 text-center">
                <p className="text-sm text-[var(--st-fg-muted)]">No scans yet.</p>
                <ButtonLink href="/dashboard/scan" className="mt-4 h-9 px-4 text-sm">
                  Run first scan
                </ButtonLink>
              </div>
            )}
          </IntelCard>
        </StaggerItem>

        {/* Latest scan live card */}
        <StaggerItem className="lg:col-span-5">
          <IntelCard
            title="Latest scan"
            description="Most recent intelligence result"
            action="Open workspace"
            actionHref="/dashboard/scan"
            accent="indigo"
            className="h-full"
          >
            {loading ? (
              <motion.div className="space-y-3">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-20 w-full rounded-xl" />
              </motion.div>
            ) : lastScan ? (
              <div className="space-y-4">
                <motion.div
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
                  className="flex flex-wrap items-center gap-2"
                >
                  <RiskBadge level={lastScan.risk_level} />
                  <span className="text-xs text-[var(--st-fg-muted)]">
                    {new Date(lastScan.scanned_at).toLocaleString()}
                  </span>
                </motion.div>
                <p className="line-clamp-3 rounded-xl border border-[var(--st-border)] bg-[var(--st-muted)]/60 p-3 font-mono text-xs leading-relaxed text-[var(--st-fg-muted)]">
                  {lastScan.input_preview || "—"}
                </p>
                <div className="flex flex-wrap gap-2">
                  <span className="rounded-lg border border-[var(--st-border)] bg-white px-2.5 py-1 font-medium capitalize text-[var(--st-fg)]">
                    {lastScan.content_type}
                  </span>
                  <span className="rounded-lg border border-[var(--st-border)] bg-white px-2.5 py-1 text-[var(--st-fg-muted)]">
                    {lastScan.finding_count} finding{lastScan.finding_count === 1 ? "" : "s"}
                  </span>
                </div>
              </div>
            ) : (
              <p className="text-sm text-[var(--st-fg-muted)]">
                Paste a prompt or model output to get an explainable risk assessment.
              </p>
            )}
          </IntelCard>
        </StaggerItem>

        {/* M365 status */}
        <StaggerItem className="lg:col-span-3">
          <IntelCard
            title="Microsoft 365"
            description="Enterprise detection"
            action="Manage"
            actionHref="/dashboard/integrations"
            accent={connected ? "neon" : "amber"}
            className="h-full"
          >
            {loading ? (
              <Skeleton className="h-24 w-full rounded-xl" />
            ) : (
              <div className="flex flex-col gap-4">
                <div className="flex items-center gap-3">
                  <div
                    className={cn(
                      "flex h-12 w-12 items-center justify-center rounded-xl",
                      connected
                        ? "bg-[var(--st-neon-subtle)] text-emerald-600"
                        : "bg-[var(--st-muted)] text-[var(--st-fg-muted)]",
                    )}
                  >
                    {connected ? (
                      <Cloud className="h-6 w-6" aria-hidden />
                    ) : (
                      <CloudOff className="h-6 w-6" aria-hidden />
                    )}
                  </div>
                  <div>
                    <p className="font-semibold capitalize text-[var(--st-fg)]">
                      {msft?.status ?? "disconnected"}
                    </p>
                    <p className="text-xs text-[var(--st-fg-muted)]">
                      {connected ? "Telemetry active" : "Connect to discover shadow AI"}
                    </p>
                  </div>
                </div>
                {!connected ? (
                  <ButtonLink href="/dashboard/integrations" className="h-9 w-full text-sm">
                    Connect M365
                  </ButtonLink>
                ) : (
                  <ButtonLink href="/dashboard/integrations" variant="secondary" className="h-9 w-full text-sm">
                    Run full detection
                  </ButtonLink>
                )}
              </div>
            )}
          </IntelCard>
        </StaggerItem>

        {/* KPI row */}
        <StaggerItem className="lg:col-span-3">
          <IntelCard title="Total scans" accent="none">
            {loading ? (
              <Skeleton className="h-10 w-20" />
            ) : (
              <p className="font-display text-4xl font-bold tabular-nums text-[var(--st-fg)]">
                {analytics?.total_scans ?? 0}
              </p>
            )}
          </IntelCard>
        </StaggerItem>
        <StaggerItem className="lg:col-span-3">
          <IntelCard title="High-risk AI events" accent="none">
            {loading ? (
              <Skeleton className="h-10 w-20" />
            ) : (
              <p className="font-display text-4xl font-bold tabular-nums text-rose-600">
                {detections?.highRiskCount ?? 0}
              </p>
            )}
          </IntelCard>
        </StaggerItem>
        <StaggerItem className="lg:col-span-3">
          <IntelCard title="AI events tracked" accent="none">
            {loading ? (
              <Skeleton className="h-10 w-20" />
            ) : (
              <p className="font-display text-4xl font-bold tabular-nums text-[var(--st-accent-secondary)]">
                {detections?.total ?? 0}
              </p>
            )}
          </IntelCard>
        </StaggerItem>
        <StaggerItem className="lg:col-span-3">
          <IntelCard title="Quick action" accent="cyan" noPadding>
            <div className="flex flex-col gap-2 p-5">
              <ButtonLink href="/dashboard/scan" className="h-10 w-full">
                <ScanSearch className="h-4 w-4" aria-hidden />
                New security scan
              </ButtonLink>
              <ButtonLink href="/dashboard/reports" variant="secondary" className="h-10 w-full">
                Generate report
              </ButtonLink>
            </div>
          </IntelCard>
        </StaggerItem>

        {/* Recent findings */}
        <StaggerItem className="lg:col-span-7">
          <IntelCard
            title="Recent findings"
            description="Top signals from your latest scan"
            action="All history"
            actionHref="/dashboard/history"
            accent="amber"
          >
            {loading ? (
              <div className="space-y-2">
                {[1, 2, 3].map((i) => (
                  <Skeleton key={i} className="h-14 w-full rounded-xl" />
                ))}
              </div>
            ) : recentHighRisk.length ? (
              <ul className="space-y-2">
                {recentHighRisk.map((item, i) => (
                  <motion.li
                    key={item.id}
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.1 }}
                    className="flex items-start gap-3 rounded-xl border border-[var(--st-border)] bg-[var(--st-muted)]/40 p-3"
                  >
                    <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-rose-500" aria-hidden />
                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-[var(--st-fg)]">{item.title}</p>
                      <p className="mt-0.5 line-clamp-2 text-xs text-[var(--st-fg-muted)]">
                        {item.subtitle}
                      </p>
                    </div>
                  </motion.li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-[var(--st-fg-muted)]">
                No high-risk activity in recent history.
              </p>
            )}
          </IntelCard>
        </StaggerItem>

        {/* Activity feed */}
        <StaggerItem className="lg:col-span-5">
          <IntelCard title="Activity pulse" description="Recent intelligence events" accent="indigo">
            {loading ? (
              <div className="space-y-2">
                {[1, 2, 4].map((i) => (
                  <Skeleton key={i} className="h-12 w-full rounded-lg" />
                ))}
              </div>
            ) : activity.length ? (
              <ul className="max-h-64 space-y-2 overflow-y-auto pr-1">
                {activity.slice(0, 8).map((item, i) => (
                  <motion.li
                    key={item.id}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className="flex items-center gap-3 rounded-lg border border-[var(--st-border)] px-3 py-2.5"
                  >
                    <TrendingUp className="h-4 w-4 shrink-0 text-[var(--st-accent)]" aria-hidden />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium text-[var(--st-fg)]">{item.title}</p>
                      <p className="text-[10px] text-[var(--st-fg-muted)]">
                        {new Date(item.occurredAt).toLocaleString()}
                      </p>
                    </div>
                    {item.riskScore != null &&
                    (item.severity === "high" ||
                      item.severity === "critical" ||
                      item.severity === "medium" ||
                      item.severity === "low") ? (
                      <RiskBadge level={item.severity} />
                    ) : null}
                  </motion.li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-[var(--st-fg-muted)]">No recent activity.</p>
            )}
          </IntelCard>
        </StaggerItem>
      </StaggerReveal>
    </div>
  );
}
