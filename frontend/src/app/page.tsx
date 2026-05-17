import Link from "next/link";
import { ArrowRight, Shield, ScanSearch, Radar } from "lucide-react";

import { publicEnv } from "@/lib/env/public";
import { ButtonLink } from "@/components/ui/button";

export default function HomePage() {
  return (
    <div className="relative min-h-screen overflow-hidden bg-[var(--st-canvas)]">
      <div className="pointer-events-none absolute inset-0 st-panel-grid opacity-80" aria-hidden />
      <div className="pointer-events-none absolute -left-32 top-20 h-96 w-96 rounded-full bg-[var(--st-mesh-1)] blur-3xl" aria-hidden />
      <div className="pointer-events-none absolute -right-32 bottom-0 h-80 w-80 rounded-full bg-[var(--st-mesh-2)] blur-3xl" aria-hidden />

      <header className="relative z-10 border-b border-[var(--st-border)]/80 bg-[var(--st-surface)]/50 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <span className="font-display text-sm font-semibold tracking-tight text-[var(--st-fg)]">
            {publicEnv.appName}
          </span>
          <nav className="flex items-center gap-2">
            <ButtonLink href="/login" variant="ghost" className="h-9 px-3">
              Sign in
            </ButtonLink>
            <ButtonLink href="/register" className="h-9 gap-1 px-3">
              Get started
              <ArrowRight className="h-4 w-4" aria-hidden />
            </ButtonLink>
          </nav>
        </div>
      </header>

      <main className="relative z-10 mx-auto flex w-full max-w-6xl flex-col gap-16 px-4 py-20 sm:px-6 lg:px-8 lg:py-28">
        <div className="max-w-3xl space-y-6 st-animate-in">
          <p className="inline-flex items-center gap-2 rounded-full border border-[var(--st-accent)]/20 bg-[var(--st-accent-subtle)] px-3 py-1 text-xs font-medium text-[var(--st-accent)]">
            <Shield className="h-3.5 w-3.5" aria-hidden />
            AI security control plane
          </p>
          <h1 className="font-display text-4xl font-bold leading-[1.1] tracking-tight text-[var(--st-fg)] sm:text-5xl lg:text-6xl">
            Govern shadow AI with{" "}
            <span className="bg-gradient-to-r from-[var(--st-accent)] to-[var(--st-accent-secondary)] bg-clip-text text-transparent">
              precision
            </span>
          </h1>
          <p className="max-w-xl text-lg leading-relaxed text-[var(--st-fg-muted)]">
            Scanlyr discovers unauthorized AI usage, scans prompts and outputs for jailbreaks and
            data exfiltration, and produces audit-ready evidence for security teams.
          </p>
          <div className="flex flex-wrap gap-3 pt-2">
            <ButtonLink href="/register" className="h-11 px-5">
              Start free
            </ButtonLink>
            <ButtonLink href="/login" variant="secondary" className="h-11 px-5">
              Sign in to console
            </ButtonLink>
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-3 st-animate-in st-animate-in-delay-1">
          {[
            {
              icon: ScanSearch,
              title: "LLM security scans",
              desc: "Prompt & output analysis with explainable risk scoring.",
            },
            {
              icon: Radar,
              title: "Shadow AI detection",
              desc: "Surface tools operating outside approved stacks.",
            },
            {
              icon: Shield,
              title: "Compliance ready",
              desc: "PDF reports and tenant-scoped audit trails.",
            },
          ].map(({ icon: Icon, title, desc }) => (
            <div
              key={title}
              className="rounded-xl border border-[var(--st-border)] bg-[var(--st-surface)]/80 p-5 backdrop-blur-sm transition hover:border-[var(--st-accent)]/30"
            >
              <Icon className="mb-3 h-6 w-6 text-[var(--st-accent)]" aria-hidden />
              <h2 className="font-display text-sm font-semibold text-[var(--st-fg)]">{title}</h2>
              <p className="mt-1 text-sm text-[var(--st-fg-muted)]">{desc}</p>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
