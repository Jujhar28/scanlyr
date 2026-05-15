/**
 * Browser-safe configuration. Only `NEXT_PUBLIC_*` variables are available here.
 * Server-only secrets must live in server modules and never be prefixed with NEXT_PUBLIC_.
 */
export const publicEnv = {
  appName: process.env.NEXT_PUBLIC_APP_NAME ?? "Scanlyr",
  apiBaseUrl:
    process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ??
    "http://localhost:8000",
} as const;
