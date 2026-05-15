"use client";

import { useState } from "react";

import { AppSidebar, MobileNavButton } from "@/components/layout/app-sidebar";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/providers/auth-provider";

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const { user, organization, signOut } = useAuth();

  return (
    <div
      data-st-console
      className="flex min-h-screen bg-[var(--st-canvas)] text-[var(--st-fg)] antialiased"
    >
      <AppSidebar mobileOpen={mobileOpen} setMobileOpen={setMobileOpen} />

      <div className="flex min-h-screen flex-1 flex-col md:pl-64">
        <header className="sticky top-0 z-30 flex h-14 items-center gap-3 border-b border-[var(--st-border)] bg-[var(--st-surface)]/85 px-4 backdrop-blur-md supports-[backdrop-filter]:bg-[var(--st-surface)]/70">
          <MobileNavButton onClick={() => setMobileOpen(true)} />
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-[var(--st-fg)]">Security console</p>
            <p className="truncate text-xs text-[var(--st-fg-muted)]">
              {organization?.name ? (
                <>
                  <span className="font-medium text-[var(--st-fg)]/90">{organization.name}</span>
                  {user ? <span className="text-[var(--st-fg-muted)]"> · {user.email}</span> : null}
                </>
              ) : user ? (
                user.email
              ) : (
                "AI visibility and compliance"
              )}
            </p>
          </div>
          <Button variant="secondary" className="h-9 px-3" type="button" onClick={() => void signOut()}>
            Sign out
          </Button>
        </header>

        <main className="st-panel-grid flex-1 px-4 py-6 sm:px-6 lg:px-8">{children}</main>
      </div>
    </div>
  );
}