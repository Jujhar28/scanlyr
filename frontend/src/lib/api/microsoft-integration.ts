import { apiFetch } from "@/lib/api/client";

export type MicrosoftGraphSyncResponse = {
  sync_run_id: string;
  status: string;
  stats: Record<string, unknown> | null;
};

/** Pull latest audit/sign-in snapshots into the tenant store before detection. */
export async function syncMicrosoft365(): Promise<MicrosoftGraphSyncResponse> {
  return apiFetch<MicrosoftGraphSyncResponse>("integrations/microsoft/sync", { method: "POST" });
}
