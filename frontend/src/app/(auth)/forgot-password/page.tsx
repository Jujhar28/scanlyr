import type { Metadata } from "next";

import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export const metadata: Metadata = {
  title: "Forgot password",
};

export default function ForgotPasswordPage() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Reset access</CardTitle>
        <CardDescription>
          Password reset will email a secure link once transactional email is
          configured.
        </CardDescription>
      </CardHeader>
      <form className="space-y-4" noValidate>
        <div className="space-y-2">
          <Label htmlFor="email">Work email</Label>
          <Input id="email" name="email" type="email" autoComplete="email" disabled />
        </div>
        <Button type="submit" className="w-full" disabled>
          Send reset link
        </Button>
      </form>
      <p className="mt-6 text-sm text-[var(--st-fg-muted)]">
        <Link href="/login" className="font-medium text-[var(--st-accent)]">
          Back to sign in
        </Link>
      </p>
    </Card>
  );
}
