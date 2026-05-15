"use client";

import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";

import { Button } from "@/components/ui/button";
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
  const { role, hydrated } = useAuth();
  const searchParams = useSearchParams();
  const isAdmin = role === "admin";

  const [status, setStatus] = useState<MicrosoftGraphStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionError, setActionError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const oauthBanner = useMemo(() => {
    const connected = searchParams.get("msft_connected");
    const err = searchParams.get("msft_error");
    const desc = searchParams.get("msft_error_description");
    if (connected === "1") {
      return { kind: "success" as const, text: "Microsoft 365 connected successfully." };
    }
    if (err) {
      return {
        kind: "error" as const,
        text: `${err}${desc ? `: ${decodeURIComponent(desc.replace(/\+/g, " "))}` : ""}`,
      };
    }
    return null;
  }, [searchParams]);

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

  useEffect(() => {
    if (!hydrated) return;
    void loadStatus();
  }, [hydrated, loadStatus]);

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
      <PageHeader
        title="Integrations"
        description="Connect Microsoft 365 to collect audit, sign-in, and enterprise app signals for governance and detection pipelines."
        actions={
          loading ? undefined : status?.status === "connected" ? (
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
              ? "rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-100"
              : "rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-100"
          }
        >
          {oauthBanner.text}
        </div>
      ) : null}

      {actionError ? (
        <div
          role="alert"
          className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-100"
        >
          {actionError}
        </div>
      ) : null}

      <Card className="overflow-hidden border-[var(--st-border)] bg-[var(--st-surface)] shadow-sm">
        <CardHeader className="border-b border-[var(--st-border)] bg-[var(--st-muted)]/30">
          <CardTitle>Microsoft 365</CardTitle>
          <CardDescription>
            OAuth is tenant-scoped; tokens are encrypted at rest. Ingestion powers AI detection and compliance
            reporting.
          </CardDescription>
        </CardHeader>
        <div className="space-y-4 p-6">
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
              <Button type="button" onClick={() => void connectMicrosoft()} disabled={busy || loading}>
                Connect Microsoft 365
              </Button>
              <Button
                type="button"
                variant="secondary"
                onClick={() => void syncNow()}
                disabled={busy || loading || status?.status !== "connected"}
              >
                Run sync now
              </Button>
              <Button
                type="button"
                variant="ghost"
                onClick={() => void disconnect()}
                disabled={busy || loading || status?.status === "disconnected"}
              >
                Disconnect
              </Button>
            </div>
          ) : (
            <p className="text-sm text-[var(--st-fg-muted)]">
              Only organization administrators can connect or modify this integration.
            </p>
          )}
        </div>
      </Card>
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
