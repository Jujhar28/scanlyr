"use client";

import { useCallback, useEffect, useState } from "react";
import { motion } from "framer-motion";
import { useParams } from "next/navigation";

import { ScanDetailView } from "@/components/scan/scan-detail-view";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError } from "@/lib/api/client";
import { fetchScanHistoryDetail, type ScanHistoryDetail } from "@/lib/api/scan-history";
import { useAuth } from "@/providers/auth-provider";

export default function ScanDetailPage() {
  const { scanId } = useParams<{ scanId: string }>();
  const { hydrated } = useAuth();
  const [detail, setDetail] = useState<ScanHistoryDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!scanId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchScanHistoryDetail(scanId);
      setDetail(data);
    } catch (e) {
      setDetail(null);
      setError(e instanceof ApiError ? e.message : "Could not load scan.");
    } finally {
      setLoading(false);
    }
  }, [scanId]);

  useEffect(() => {
    if (!hydrated) return;
    void load();
  }, [hydrated, load]);

  if (!hydrated) return null;

  if (loading) {
    return (
      <div className="mx-auto max-w-[1680px] space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-64 w-full rounded-2xl" />
      </div>
    );
  }

  if (error || !detail) {
    return (
      <motion.div
        role="alert"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-xl border border-rose-500/30 bg-rose-50 px-4 py-3 text-sm text-rose-800"
      >
        {error ?? "Scan not found."}
      </motion.div>
    );
  }

  return <ScanDetailView detail={detail} />;
}
