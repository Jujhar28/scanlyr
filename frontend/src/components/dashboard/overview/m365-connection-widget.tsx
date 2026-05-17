"use client";

import Link from "next/link";
import { Cloud, CloudOff, Loader2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { ButtonLink } from "@/components/ui/button";
import type { MicrosoftOverviewStatus } from "@/lib/overview/types";

import { OverviewEmptyState, OverviewWidget } from "./overview-widget";

function statusVariant(status: string): "success" | "warning" | "outline" | "danger" {
  if (status === "connected") return "success";
  if (status === "pending") return "warning";
  if (status === "error") return "danger";
  return "outline";
}

function formatWhen(iso: string | null): string {
  if (!iso) return "Never";
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function M365ConnectionWidget({
  msft,
  loading,
}: {
  msft: MicrosoftOverviewStatus | null;
  loading?: boolean;
}) {
  const connected = msft?.status === "connected";

  return (
    <OverviewWidget
      title="Microsoft 365"
      description="Tenant connection for shadow AI detection"
      action="Manage"
      actionHref="/dashboard/integrations"
      loading={loading}
      empty={
        <OverviewEmptyState
          message="Connect Microsoft 365 to discover ungoverned AI tools across your tenant."
          action="Connect integration"
          actionHref="/dashboard/integrations"
        />
      }
    >
      {msft ? (
        <div className="flex flex-col gap-4">
          <div className="flex items-start gap-3">
            <div
              className={
                connected
                  ? "flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-500/15 text-emerald-400"
                  : "flex h-12 w-12 items-center justify-center rounded-xl bg-[var(--st-muted)] text-[var(--st-fg-muted)]"
              }
            >
              {connected ? <Cloud className="h-6 w-6" aria-hidden /> : <CloudOff className="h-6 w-6" aria-hidden />}
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant={statusVariant(msft.status)} className="normal-case">
                  {msft.status}
                </Badge>
                {msft.status === "pending" ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin text-amber-400" aria-hidden />
                ) : null}
              </div>
              <p className="mt-2 text-sm text-[var(--st-fg)]">
                {connected
                  ? "Telemetry linked. Run a full scan to refresh AI events."
                  : "Not connected — detection pipeline is idle."}
              </p>
            </div>
          </div>

          <dl className="grid gap-2 text-sm sm:grid-cols-2">
            <div className="rounded-lg bg-[var(--st-muted)]/40 px-3 py-2">
              <dt className="text-xs text-[var(--st-fg-muted)]">Connected</dt>
              <dd className="mt-0.5 font-medium tabular-nums">{formatWhen(msft.connected_at)}</dd>
            </div>
            <div className="rounded-lg bg-[var(--st-muted)]/40 px-3 py-2">
              <dt className="text-xs text-[var(--st-fg-muted)]">Last sync</dt>
              <dd className="mt-0.5 font-medium tabular-nums">{formatWhen(msft.last_sync_at)}</dd>
            </div>
          </dl>

          {msft.last_error_message ? (
            <p className="rounded-lg border border-red-500/25 bg-red-500/10 px-3 py-2 text-xs text-red-100">
              {msft.last_error_message}
            </p>
          ) : null}

          {!connected ? (
            <ButtonLink href="/dashboard/integrations" className="h-9 w-full text-sm sm:w-auto">
              Connect Microsoft 365
            </ButtonLink>
          ) : (
            <Link
              href="/dashboard/integrations"
              className="text-center text-sm font-medium text-[var(--st-accent)] hover:underline sm:text-left"
            >
              Manage integrations →
            </Link>
          )}
        </div>
      ) : null}
    </OverviewWidget>
  );
}
