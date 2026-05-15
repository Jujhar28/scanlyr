"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { getAccessToken } from "@/lib/auth/token-store";
import { useAuth } from "@/providers/auth-provider";

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { hydrated } = useAuth();

  useEffect(() => {
    if (!hydrated) return;
    if (!getAccessToken()) {
      router.replace("/login");
    }
  }, [hydrated, router]);

  if (!hydrated) {
    return (
      <div className="flex flex-1 items-center justify-center text-sm text-[var(--st-fg-muted)]">
        Checking your session…
      </div>
    );
  }

  if (!getAccessToken()) {
    return null;
  }

  return <>{children}</>;
}
