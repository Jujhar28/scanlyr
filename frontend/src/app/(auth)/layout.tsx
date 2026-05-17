import Link from "next/link";
import { Shield } from "lucide-react";

import { publicEnv } from "@/lib/env/public";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="st-auth-mesh relative flex min-h-screen flex-col overflow-hidden">
      <div className="pointer-events-none absolute inset-0 st-scanline opacity-30" aria-hidden />
      <header className="relative z-10 border-b border-[var(--st-border)] bg-[var(--st-surface)]/60 px-4 py-4 backdrop-blur-md sm:px-6">
        <Link href="/" className="inline-flex items-center gap-2.5">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-[var(--st-accent-subtle)] text-[var(--st-accent)] ring-1 ring-[var(--st-accent)]/20">
            <Shield className="h-5 w-5" aria-hidden />
          </span>
          <span className="font-display text-sm font-semibold tracking-tight text-[var(--st-fg)]">
            {publicEnv.appName}
          </span>
        </Link>
      </header>
      <div className="relative z-10 flex flex-1 items-center justify-center px-4 py-10 sm:px-6">
        <div className="w-full max-w-md st-animate-in">{children}</div>
      </div>
    </div>
  );
}
