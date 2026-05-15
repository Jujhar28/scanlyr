"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect } from "react";
import { Menu, Shield, X } from "lucide-react";

import { dashboardNav } from "@/config/navigation";
import { publicEnv } from "@/lib/env/public";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils/cn";
import { useAuth } from "@/providers/auth-provider";

type AppSidebarProps = {
  mobileOpen: boolean;
  setMobileOpen: (open: boolean) => void;
};

export function AppSidebar({ mobileOpen, setMobileOpen }: AppSidebarProps) {
  const pathname = usePathname();
  const { organization, role } = useAuth();

  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  return (
    <>
      {mobileOpen ? (
        <button
          type="button"
          aria-label="Close navigation"
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm md:hidden"
          onClick={() => setMobileOpen(false)}
        />
      ) : null}

      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-[var(--st-border)] bg-[var(--st-sidebar)] shadow-[4px_0_24px_rgba(0,0,0,0.35)] transition-transform duration-200 md:translate-x-0",
          mobileOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0",
        )}
      >
        <div className="flex h-14 items-center gap-2 border-b border-[var(--st-border)] px-4">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[var(--st-accent-subtle)] text-[var(--st-accent)] ring-1 ring-cyan-400/20">
            <Shield className="h-5 w-5" aria-hidden />
          </div>
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold tracking-tight text-[var(--st-fg)]">
              {publicEnv.appName}
            </p>
            <p className="truncate text-xs text-[var(--st-fg-muted)]">AI governance</p>
          </div>
          <button
            type="button"
            className="ml-auto rounded-md p-2 text-[var(--st-fg-muted)] hover:bg-[var(--st-muted)] md:hidden"
            onClick={() => setMobileOpen(false)}
            aria-label="Close menu"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav className="flex-1 space-y-0.5 overflow-y-auto p-2" aria-label="Primary">
          {dashboardNav.map((item) => {
            const active =
              item.href === "/dashboard"
                ? pathname === "/dashboard"
                : pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                  active
                    ? "border-l-2 border-l-[var(--st-accent)] bg-[var(--st-muted)] text-[var(--st-fg)] shadow-sm"
                    : "border-l-2 border-l-transparent text-[var(--st-fg-muted)] hover:bg-[var(--st-muted)]/80 hover:text-[var(--st-fg)]",
                )}
              >
                <item.icon
                  className={cn(
                    "h-4 w-4 shrink-0 transition-colors",
                    active ? "text-[var(--st-accent)]" : "text-[var(--st-fg-muted)] group-hover:text-[var(--st-fg)]",
                  )}
                  aria-hidden
                />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="border-t border-[var(--st-border)] p-3">
          <p className="truncate text-xs font-medium text-[var(--st-fg)]">{organization?.name ?? "Organization"}</p>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            {role ? (
              <Badge variant="accent" className="normal-case tracking-normal">
                {role}
              </Badge>
            ) : null}
            <span className="text-[10px] uppercase tracking-wider text-[var(--st-fg-muted)]">Tenant</span>
          </div>
        </div>
      </aside>
    </>
  );
}

export function MobileNavButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      type="button"
      className="inline-flex rounded-md p-2 text-[var(--st-fg-muted)] hover:bg-[var(--st-muted)] md:hidden"
      onClick={onClick}
      aria-label="Open navigation"
    >
      <Menu className="h-5 w-5" />
    </button>
  );
}
