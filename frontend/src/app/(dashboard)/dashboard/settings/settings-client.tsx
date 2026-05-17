"use client";

import { PageHeader } from "@/components/dashboard/page-header";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useAuth } from "@/providers/auth-provider";

export function SettingsPageClient() {
  const { user, organization, role, hydrated } = useAuth();

  if (!hydrated) {
    return null;
  }

  return (
    <div className="mx-auto max-w-[1600px] space-y-8">
      <PageHeader
        title="Profile & organization"
        description="Your account, tenant context, and session details for audit attribution."
        actions={role ? <Badge variant="accent">{role}</Badge> : null}
      />

      <div className="flex flex-col gap-4 rounded-xl border border-[var(--st-border)] bg-gradient-to-br from-[var(--st-surface)] to-[var(--st-muted)]/30 p-6 sm:flex-row sm:items-center">
        <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl bg-[var(--st-accent-subtle)] font-display text-2xl font-bold text-[var(--st-accent)] ring-1 ring-[var(--st-accent)]/25">
          {(user?.full_name?.[0] ?? user?.email?.[0] ?? "?").toUpperCase()}
        </div>
        <div className="min-w-0">
          <p className="font-display text-xl font-semibold text-[var(--st-fg)]">
            {user?.full_name ?? user?.email ?? "User"}
          </p>
          <p className="text-sm text-[var(--st-fg-muted)]">{user?.email}</p>
          <p className="mt-1 text-xs text-[var(--st-fg-muted)]">
            {organization?.name} · {role ?? "member"}
          </p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="border-[var(--st-border)] bg-[var(--st-surface)] shadow-sm">
          <CardHeader className="border-b border-[var(--st-border)] bg-[var(--st-muted)]/30">
            <CardTitle>Organization</CardTitle>
            <CardDescription>Active tenant for this session.</CardDescription>
          </CardHeader>
          <dl className="space-y-4 p-6 text-sm">
            <div>
              <dt className="text-xs uppercase tracking-wider text-[var(--st-fg-muted)]">Name</dt>
              <dd className="mt-1 text-lg font-semibold text-[var(--st-fg)]">{organization?.name ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wider text-[var(--st-fg-muted)]">Slug</dt>
              <dd className="mt-1 font-mono text-[var(--st-fg-muted)]">{organization?.slug ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wider text-[var(--st-fg-muted)]">Organization ID</dt>
              <dd className="mt-1 break-all font-mono text-xs text-[var(--st-fg-muted)]">{organization?.id ?? "—"}</dd>
            </div>
          </dl>
        </Card>

        <Card className="border-[var(--st-border)] bg-[var(--st-surface)] shadow-sm">
          <CardHeader className="border-b border-[var(--st-border)] bg-[var(--st-muted)]/30">
            <CardTitle>Your account</CardTitle>
            <CardDescription>Signed-in user for audit attribution.</CardDescription>
          </CardHeader>
          <dl className="space-y-4 p-6 text-sm">
            <div>
              <dt className="text-xs uppercase tracking-wider text-[var(--st-fg-muted)]">Email</dt>
              <dd className="mt-1 font-medium text-[var(--st-fg)]">{user?.email ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wider text-[var(--st-fg-muted)]">Display name</dt>
              <dd className="mt-1 text-[var(--st-fg-muted)]">{user?.full_name ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wider text-[var(--st-fg-muted)]">Status</dt>
              <dd className="mt-1">
                <Badge variant={user?.is_active ? "success" : "danger"}>{user?.is_active ? "Active" : "Inactive"}</Badge>
              </dd>
            </div>
          </dl>
        </Card>
      </div>

      <Card className="border-[var(--st-border)] border-dashed bg-[var(--st-muted)]/20 shadow-none">
        <CardHeader>
          <CardTitle>Coming soon</CardTitle>
          <CardDescription>
            Session timeout, IP allow lists, SCIM, data residency, and retention policies will appear in this
            module.
          </CardDescription>
        </CardHeader>
      </Card>
    </div>
  );
}
