"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Activity } from "lucide-react";

import { AppSidebar, MobileNavButton } from "@/components/layout/app-sidebar";
import { Button, ButtonLink } from "@/components/ui/button";
import { useAuth } from "@/providers/auth-provider";

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const { user, organization, signOut } = useAuth();

  return (
    <motion.div
      data-st-console
      className="st-grain relative flex min-h-screen bg-[var(--st-canvas)] text-[var(--st-fg)] antialiased"
    >
      <AppSidebar mobileOpen={mobileOpen} setMobileOpen={setMobileOpen} />

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
        className="relative z-10 flex min-h-screen flex-1 flex-col md:pl-[17rem]"
      >
        <header className="sticky top-0 z-30 flex h-14 items-center gap-3 border-b border-[var(--st-border)] bg-[var(--st-surface)]/90 px-4 backdrop-blur-xl supports-[backdrop-filter]:bg-[var(--st-surface)]/80">
          <MobileNavButton onClick={() => setMobileOpen(true)} />
          <div className="flex min-w-0 flex-1 items-center gap-2">
            <span className="hidden h-8 w-8 items-center justify-center rounded-lg bg-[var(--st-accent-subtle)] text-[var(--st-accent)] sm:flex">
              <Activity className="h-4 w-4" aria-hidden />
            </span>
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
              className="min-w-0"
            >
              <p className="truncate font-display text-sm font-semibold text-[var(--st-fg)]">
                {organization?.name ?? "Command center"}
              </p>
              <p className="truncate text-xs text-[var(--st-fg-muted)]">
                {user?.email ?? "Live security intelligence"}
              </p>
            </motion.div>
          </div>
          <div className="flex items-center gap-2">
            <ButtonLink
              href="/dashboard/scan"
              className="hidden h-9 px-3 text-sm sm:inline-flex"
            >
              Run scan
            </ButtonLink>
            <ButtonLink
              href="/dashboard/settings"
              variant="ghost"
              className="hidden h-9 px-3 sm:inline-flex"
            >
              Profile
            </ButtonLink>
            <Button
              variant="secondary"
              className="h-9 px-3 text-sm"
              type="button"
              onClick={() => void signOut()}
            >
              Sign out
            </Button>
          </div>
        </header>

        <main className="st-panel-grid flex-1 px-4 py-6 sm:px-6 lg:px-8">{children}</main>
      </motion.div>
    </motion.div>
  );
}
