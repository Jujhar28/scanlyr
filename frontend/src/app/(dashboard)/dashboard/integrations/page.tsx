"use client";

import { Suspense, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { motion } from "framer-motion";
import { useRouter, useSearchParams } from "next/navigation";

import { MicrosoftFullScanCard } from "@/components/integrations/microsoft-full-scan-card";
import { Button } from "@/components/ui/button";
import { IntelCard, PageHero } from "@/components/intel";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useMicrosoftFullScan } from "@/hooks/use-microsoft-full-scan";
import { apiFetch, ApiError } from "@/lib/api/client";
import { storeFullScanSuccess } from "@/lib/full-scan/session";
import { useToast } from "@/providers/toast-provider";
import { useAuth } from "@/providers/auth-provider";

type MicrosoftGraphStatus = {
  status: string;
  azure_tenant_id: string | null;
  last_sync_at: string | null;
  last_error_message: string | null;
  connected_at: string | null;
  scopes: string | null;
  recent_sync: {
    id: string;
    started_at: string;
    completed_at: string | null;
    status: string;
    stats: Record<string, unknown> | null;
    error_message: string | null;
  } | null;
};

type ConnectResponse = {
  authorization_url: string;
};

function IntegrationsPageInner() {
  const router = useRouter();
  const { toast } = useToast();
  const { role, hydrated } = useAuth();
  const searchParams = useSearchParams();
  const isAdmin = role === "admin";

  const [status, setStatus] = useState<MicrosoftGraphStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionError, setActionError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const fullScan = useMicrosoftFullScan();
  const autoScanStarted = useRef(false);

  const oauthBanner = useMemo(() => {
    const connected = searchParams.get("msft_connected");
    const err = searchParams.get("msft_error");
    const desc = searchParams.get("msft_error_description");
    if (connected === "1") {
      return {
        kind: "success" as const,
        text: "Microsoft 365 connected. Starting your first full scan…",
      };
    }
    if (err) {
      return {
        kind: "error" as const,
        text: `${err}${desc ? `: ${decodeURIComponent(desc.replace(/\+/g, " "))}` : ""}`,
      };
    }
    return null;
  }, [searchParams]);

  const isConnected = status?.status === "connected";

  const loadStatus = useCallback(async () => {
    setLoading(true);
    setActionError(null);
    try {
      const data = await apiFetch<MicrosoftGraphStatus>("integrations/microsoft/status");
      setStatus(data);
    } catch (e) {
      setActionError(e instanceof ApiError ? e.message : "Failed to load integration status.");
    } finally {
      setLoading(false);
    }
  }, []);

  const finishFullScan = useCallback(
    async (redirect: boolean) => {
      try {
        const pipeline = await fullScan.run();
        storeFullScanSuccess(pipeline);
        await loadStatus();
        if (redirect) {
          router.push("/dashboard/detections?full_scan=1");
        } else {
          const inserted = pipeline.detection_events_inserted;
          toast({
            variant: "success",
            title: "Full scan complete",
            description:
              inserted > 0
                ? `${inserted} new AI event${inserted === 1 ? "" : "s"} recorded. Compliance report ready.`
                : "Scan finished. No new AI events matched rules this run.",
          });
        }
      } catch (e) {
        toast({
          variant: "error",
          title: "Full scan failed",
          description: e instanceof ApiError ? e.message : "Could not complete the scan pipeline.",
        });
      }
    },
    [fullScan.run, loadStatus, router, toast],
  );

  useEffect(() => {
    if (!hydrated) return;
    void loadStatus();
  }, [hydrated, loadStatus]);

  useEffect(() => {
    if (!hydrated || !isAdmin || loading || fullScan.isRunning) return;
    if (searchParams.get("msft_connected") !== "1") return;
    if (!isConnected) return;
    if (autoScanStarted.current) return;

    autoScanStarted.current = true;
    router.replace("/dashboard/integrations");
    void finishFullScan(true);
  }, [
    hydrated,
    isAdmin,
    loading,
    isConnected,
    searchParams,
    router,
    finishFullScan,
    fullScan.isRunning,
  ]);

  async function connectMicrosoft() {
    setBusy(true);
    setActionError(null);
    try {
      const res = await apiFetch<ConnectResponse>("integrations/microsoft/connect", {
        method: "POST",
      });
      window.location.assign(res.authorization_url);
    } catch (e) {
      setActionError(e instanceof ApiError ? e.message : "Could not start Microsoft sign-in.");
      setBusy(false);
    }
  }

  async function syncNow() {
    setBusy(true);
    setActionError(null);
    try {
      await apiFetch("integrations/microsoft/sync", { method: "POST" });
      await loadStatus();
    } catch (e) {
      setActionError(e instanceof ApiError ? e.message : "Sync failed.");
    } finally {
      setBusy(false);
    }
  }

  async function disconnect() {
    setBusy(true);
    setActionError(null);
    try {
      await apiFetch("integrations/microsoft/disconnect", { method: "DELETE" });
      fullScan.reset();
      await loadStatus();
    } catch (e) {
      setActionError(e instanceof ApiError ? e.message : "Disconnect failed.");
    } finally {
      setBusy(false);
    }
  }

  if (!hydrated) {
    return null;
  }

  return (
    <div className="mx-auto max-w-[1600px] space-y-6">
      <PageHero
        eyebrow="Enterprise"
        title="Integrations"
        description="Connect Microsoft 365, run full tenant detection, and sync shadow-AI telemetry."
        actions={
          loading ? undefined : isConnected ? (
            <Badge variant="success" className="normal-case">
              Connected
            </Badge>
          ) : status?.status === "pending" ? (
            <Badge variant="warning" className="normal-case">
              Pending OAuth
            </Badge>
          ) : (
            <Badge variant="outline" className="normal-case">
              Disconnected
            </Badge>
          )
        }
      />

      {oauthBanner ? (
        <div
          role="status"
          className={
            oauthBanner.kind === "success"
              ? "rounded-xl border border-emerald-500/30 bg-emerald-50 px-4 py-3 text-sm text-emerald-800"
              : "rounded-xl border border-rose-500/30 bg-rose-50 px-4 py-3 text-sm text-rose-800"
          }
        >
          {oauthBanner.text}
        </div>
      ) : null}

      {actionError ? (
        <div
          role="alert"
          className="rounded-xl border border-rose-500/30 bg-rose-50 px-4 py-3 text-sm text-rose-800"
        >
          {actionError}
        </div>
      ) : null}

      {!loading && isConnected ? (
        <MicrosoftFullScanCard
          connected={isConnected}
          isAdmin={isAdmin}
          phase={fullScan.phase}
          progress={fullScan.progress}
          error={fullScan.error}
          isRunning={fullScan.isRunning}
          onRun={() => finishFullScan(true)}
        />
      ) : null}

      <IntelCard title="Microsoft 365" description="OAuth · sync status · connection controls" accent="indigo">
        <motion.div className="space-y-4">
          {loading ? (
            <div className="grid gap-4 sm:grid-cols-2">
              {[1, 2, 3, 4].map((i) => (
                <Skeleton key={i} className="h-14 rounded-lg" />
              ))}
            </div>
          ) : status ? (
            <dl className="grid gap-3 text-sm sm:grid-cols-2">
              <div>
                <dt className="text-[var(--st-fg-muted)]">Status</dt>
                <dd className="font-medium capitalize">{status.status}</dd>
              </div>
              <div>
                <dt className="text-[var(--st-fg-muted)]">Azure tenant ID</dt>
                <dd className="font-mono text-xs break-all">{status.azure_tenant_id ?? "—"}</dd>
              </div>
              <div>
                <dt className="text-[var(--st-fg-muted)]">Connected</dt>
                <dd>{status.connected_at ? new Date(status.connected_at).toLocaleString() : "—"}</dd>
              </div>
              <div>
                <dt className="text-[var(--st-fg-muted)]">Last sync</dt>
                <dd>{status.last_sync_at ? new Date(status.last_sync_at).toLocaleString() : "—"}</dd>
              </div>
              {status.last_error_message ? (
                <div className="sm:col-span-2">
                  <dt className="text-[var(--st-fg-muted)]">Last error</dt>
                  <dd className="text-red-200">{status.last_error_message}</dd>
                </div>
              ) : null}
              {status.recent_sync ? (
                <div className="sm:col-span-2 rounded-md border border-[var(--st-border)] bg-[var(--st-muted)]/40 p-3">
                  <p className="text-xs font-semibold uppercase tracking-wide text-[var(--st-fg-muted)]">
                    Recent sync
                  </p>
                  <p className="mt-1 text-sm">
                    {status.recent_sync.status} · started{" "}
                    {new Date(status.recent_sync.started_at).toLocaleString()}
                  </p>
                  {status.recent_sync.stats ? (
                    <pre className="mt-2 max-h-40 overflow-auto rounded bg-black/30 p-2 text-xs text-[var(--st-fg-muted)]">
                      {JSON.stringify(status.recent_sync.stats, null, 2)}
                    </pre>
                  ) : null}
                </div>
              ) : null}
            </dl>
          ) : null}

          {isAdmin ? (
            <div className="flex flex-wrap gap-2 pt-2">
              <Button type="button" onClick={() => void connectMicrosoft()} disabled={busy || loading || fullScan.isRunning}>
                Connect Microsoft 365
              </Button>
              <Button
                type="button"
                variant="secondary"
                onClick={() => void syncNow()}
                disabled={busy || loading || !isConnected || fullScan.isRunning}
              >
                Sync telemetry only
              </Button>
              <Button
                type="button"
                variant="ghost"
                onClick={() => void disconnect()}
                disabled={busy || loading || status?.status === "disconnected" || fullScan.isRunning}
              >
                Disconnect
              </Button>
            </div>
          ) : (
            <p className="text-sm text-[var(--st-fg-muted)]">
              Only organization administrators can connect or modify this integration.
            </p>
          )}
        </motion.div>
      </IntelCard>
    </div>
  );
}

export default function IntegrationsPage() {
  return (
    <Suspense
      fallback={
        <div className="mx-auto max-w-[1600px] p-6 text-sm text-[var(--st-fg-muted)]">Loading…</div>
      }
    >
      <IntegrationsPageInner />
    </Suspense>
  );
}
