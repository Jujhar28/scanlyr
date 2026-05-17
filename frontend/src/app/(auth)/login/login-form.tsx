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

export function LoginForm() {
  const { signInWithSession } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setPending(true);
    try {
      const session = await apiFetch<AuthSession>("auth/login", {
        method: "POST",
        json: { email, password },
        auth: false,
      });
      signInWithSession(session);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to sign in");
    } finally {
      setPending(false);
    }
  }

  return (
    <Card className="border-[var(--st-border)] bg-[var(--st-surface)]/90 shadow-2xl shadow-black/40 ring-1 ring-white/5 backdrop-blur-xl">
      <CardHeader>
        <CardTitle className="font-display">Sign in</CardTitle>
        <CardDescription>
          Use the email and password for your Scanlyr organization account.
        </CardDescription>
      </CardHeader>
      <form className="space-y-4" onSubmit={onSubmit} noValidate>
        {error ? (
          <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800 dark:border-red-900/60 dark:bg-red-950/40 dark:text-red-100">
            {error}
          </p>
        ) : null}
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
          <Label htmlFor="password">Password</Label>
          <Input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(ev) => setPassword(ev.target.value)}
            required
          />
        </div>
        <Button type="submit" className="w-full" disabled={pending}>
          {pending ? "Signing in…" : "Continue"}
        </Button>
      </form>
      <div className="mt-6 flex flex-col gap-2 text-sm text-[var(--st-fg-muted)]">
        <Link href="/forgot-password" className="hover:text-[var(--st-fg)]">
          Forgot password?
        </Link>
        <p>
          Need an account?{" "}
          <Link href="/register" className="font-medium text-[var(--st-accent)]">
            Register
          </Link>
        </p>
      </div>
    </Card>
  );
}
