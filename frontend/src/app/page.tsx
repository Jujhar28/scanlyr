import { publicEnv } from "@/lib/env/public";
import { ButtonLink } from "@/components/ui/button";

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col bg-[var(--st-canvas)]">
      <header className="border-b border-[var(--st-border)] bg-[var(--st-surface)]">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <span className="text-sm font-semibold tracking-tight">
            {publicEnv.appName}
          </span>
          <nav className="flex items-center gap-2">
            <ButtonLink href="/login" variant="ghost" className="h-9 px-3">
              Sign in
            </ButtonLink>
            <ButtonLink href="/dashboard" className="h-9 px-3">
              Open console
            </ButtonLink>
          </nav>
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col justify-center gap-8 px-4 py-16 sm:px-6 lg:px-8">
        <div className="max-w-2xl space-y-4">
          <p className="text-sm font-medium text-[var(--st-accent)]">
            Shadow AI governance
          </p>
          <h1 className="text-3xl font-semibold tracking-tight text-[var(--st-fg)] sm:text-4xl">
            Find AI tools operating outside your approved stack.
          </h1>
          <p className="text-base leading-relaxed text-[var(--st-fg-muted)]">
            Scanlyr is the control plane for discovery, policy alignment, and
            audit-ready reporting. This interface is scaffolded for product work
            ahead—navigation, layouts, and API wiring are in place.
          </p>
        </div>
      </main>
    </div>
  );
}
