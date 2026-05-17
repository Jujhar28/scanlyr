"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect } from "react";
import { motion } from "framer-motion";
import { Menu, Radar, Shield, X, Zap } from "lucide-react";

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
  }, [pathname, setMobileOpen]);

  return (
    <>
      {mobileOpen ? (
        <button
          type="button"
          aria-label="Close navigation"
          className="fixed inset-0 z-40 bg-[var(--st-sidebar)]/60 backdrop-blur-sm md:hidden"
          onClick={() => setMobileOpen(false)}
        />
      ) : null}

      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex w-[17rem] flex-col border-r border-white/5 bg-[var(--st-sidebar)] text-[var(--st-sidebar-fg)] shadow-2xl transition-transform duration-300 md:translate-x-0",
          mobileOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0",
        )}
      >
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
          className="relative flex h-16 items-center gap-3 border-b border-white/8 px-4"
        >
          <div className="absolute inset-x-0 bottom-0 h-px bg-gradient-to-r from-transparent via-[var(--st-accent)]/50 to-transparent" />
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--st-accent)]/15 text-[var(--st-accent)] ring-1 ring-[var(--st-accent)]/30">
            <Shield className="h-5 w-5" aria-hidden />
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate font-display text-sm font-bold tracking-tight">
              {publicEnv.appName}
            </p>
            <p className="flex items-center gap-1 truncate text-[10px] uppercase tracking-widest text-[var(--st-sidebar-muted)]">
              <Zap className="h-3 w-3 text-[var(--st-neon)]" aria-hidden />
              Cyber intelligence
            </p>
          </div>
          <button
            type="button"
            className="ml-auto rounded-md p-2 text-[var(--st-sidebar-muted)] hover:bg-white/5 md:hidden"
            onClick={() => setMobileOpen(false)}
            aria-label="Close menu"
          >
            <X className="h-5 w-5" />
          </button>
        </motion.div>

        <nav className="flex-1 space-y-1 overflow-y-auto p-3" aria-label="Primary">
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
                  "group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200",
                  active
                    ? "bg-white/10 text-white shadow-inner"
                    : "text-[var(--st-sidebar-muted)] hover:bg-white/5 hover:text-white",
                )}
              >
                {active ? (
                  <span className="absolute left-0 top-1/2 h-6 w-0.5 -translate-y-1/2 rounded-full bg-[var(--st-accent)]" />
                ) : null}
                <item.icon
                  className={cn(
                    "h-4 w-4 shrink-0",
                    active ? "text-[var(--st-accent)]" : "text-[var(--st-sidebar-muted)] group-hover:text-white",
                  )}
                  aria-hidden
                />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="border-t border-white/8 p-4">
          <div className="rounded-xl bg-white/5 p-3 ring-1 ring-white/8">
            <p className="truncate text-xs font-medium text-white/90">
              {organization?.name ?? "Organization"}
            </p>
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
              className="mt-2 flex items-center gap-2"
            >
              {role ? (
                <Badge variant="accent" className="normal-case tracking-normal">
                  {role}
                </Badge>
              ) : null}
              <span className="inline-flex items-center gap-1 text-[10px] text-[var(--st-sidebar-muted)]">
                <Radar className="h-3 w-3 text-[var(--st-neon)]" aria-hidden />
                Live
              </span>
            </motion.div>
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
      className="inline-flex rounded-lg p-2 text-[var(--st-fg-muted)] hover:bg-[var(--st-muted)] md:hidden"
      onClick={onClick}
      aria-label="Open navigation"
    >
      <Menu className="h-5 w-5" />
    </button>
  );
}
