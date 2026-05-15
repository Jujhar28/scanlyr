"use client";

import { useState } from "react";
import Link from "next/link";

import { apiFetch, ApiError } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { AuthSession } from "@/lib/auth/types";
import { useAuth } from "@/providers/auth-provider";

export function RegisterForm() {
  const { signInWithSession } = useAuth();
  const [organizationName, setOrganizationName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setPending(true);
    try {
      const session = await apiFetch<AuthSession>("auth/register", {
        method: "POST",
        json: {
          organization_name: organizationName,
          email,
          password,
          full_name: fullName || null,
        },
        auth: false,
      });
      signInWithSession(session);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to create account");
    } finally {
      setPending(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Create organization</CardTitle>
        <CardDescription>
          Creates your tenant, default roles, and an administrator membership for your user.
        </CardDescription>
      </CardHeader>
      <form className="space-y-4" onSubmit={onSubmit} noValidate>
        {error ? (
          <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800 dark:border-red-900/60 dark:bg-red-950/40 dark:text-red-100">
            {error}
          </p>
        ) : null}
        <div className="space-y-2">
          <Label htmlFor="org">Organization name</Label>
          <Input
            id="org"
            name="org"
            type="text"
            autoComplete="organization"
            value={organizationName}
            onChange={(ev) => setOrganizationName(ev.target.value)}
            required
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="email">Work email</Label>
          <Input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(ev) => setEmail(ev.target.value)}
            required
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="full_name">Full name (optional)</Label>
          <Input
            id="full_name"
            name="full_name"
            type="text"
            autoComplete="name"
            value={fullName}
            onChange={(ev) => setFullName(ev.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="password">Password</Label>
          <Input
            id="password"
            name="password"
            type="password"
            autoComplete="new-password"
            value={password}
            onChange={(ev) => setPassword(ev.target.value)}
            required
          />
          <p className="text-xs text-[var(--st-fg-muted)]">
            At least 8 characters, including letters and numbers.
          </p>
        </div>
        <Button type="submit" className="w-full" disabled={pending}>
          {pending ? "Creating…" : "Create account"}
        </Button>
      </form>
      <p className="mt-6 text-sm text-[var(--st-fg-muted)]">
        Already have access?{" "}
        <Link href="/login" className="font-medium text-[var(--st-accent)]">
          Sign in
        </Link>
      </p>
    </Card>
  );
}
