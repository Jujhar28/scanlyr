import { publicEnv } from "@/lib/env/public";
import { getAccessToken } from "@/lib/auth/token-store";

import type { ApiErrorBody, HttpMethod } from "./types";

const API_PREFIX = "/api/v1";

export class ApiError extends Error {
  readonly status: number;
  readonly body: unknown;

  constructor(message: string, status: number, body: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

export type ApiClientOptions = Omit<RequestInit, "body" | "method"> & {
  method?: HttpMethod;
  /** JSON-serializable body for non-GET requests */
  json?: unknown;
  /** Skip JSON Content-Type (e.g. FormData uploads later) */
  skipJsonHeaders?: boolean;
  /** When false, do not attach `Authorization` even if an access token exists */
  auth?: boolean;
};

function buildUrl(path: string): string {
  const base = publicEnv.apiBaseUrl.replace(/\/$/, "");
  if (path.startsWith("http://") || path.startsWith("https://")) {
    return path;
  }
  if (path.startsWith("/api/")) {
    return `${base}${path}`;
  }
  if (path.startsWith("/")) {
    return `${base}${path}`;
  }
  const trimmed = path.replace(/^\/+/, "");
  return `${base}${API_PREFIX}/${trimmed}`;
}

function extractErrorMessage(parsed: unknown, fallback: string): string {
  if (typeof parsed === "string" && parsed.trim()) {
    return parsed;
  }
  if (typeof parsed === "object" && parsed !== null) {
    const body = parsed as ApiErrorBody;
    if (typeof body.message === "string" && body.message.trim()) {
      return body.message;
    }
    if (typeof body.detail === "string" && body.detail.trim()) {
      return body.detail;
    }
    const details = body.details as { errors?: Array<{ msg?: string }> } | undefined;
    const first = details?.errors?.[0]?.msg;
    if (typeof first === "string" && first.trim()) {
      return first;
    }
  }
  return fallback;
}

/**
 * Typed fetch wrapper for the FastAPI backend (Bearer access token when available).
 */
export async function apiFetch<T>(
  path: string,
  { json, skipJsonHeaders, headers, auth = true, ...init }: ApiClientOptions = {},
): Promise<T> {
  const url = buildUrl(path);
  const mergedHeaders = new Headers(headers);

  if (auth) {
    const token = getAccessToken();
    if (token && !mergedHeaders.has("Authorization")) {
      mergedHeaders.set("Authorization", `Bearer ${token}`);
    }
  }

  let body: BodyInit | undefined;
  if (json !== undefined) {
    body = JSON.stringify(json);
    if (!skipJsonHeaders && !mergedHeaders.has("Content-Type")) {
      mergedHeaders.set("Content-Type", "application/json");
    }
  }

  const response = await fetch(url, {
    ...init,
    headers: mergedHeaders,
    body,
    cache: init.cache ?? "no-store",
    credentials: init.credentials ?? "include",
  });

  if (response.status === 204) {
    return undefined as T;
  }

  const contentType = response.headers.get("content-type") ?? "";
  const isJson = contentType.includes("application/json");
  const parsed = isJson ? await response.json().catch(() => null) : await response.text();

  if (!response.ok) {
    const message = extractErrorMessage(parsed, response.statusText);
    throw new ApiError(message, response.status, parsed);
  }

  return parsed as T;
}

/** Authenticated GET returning a Blob (e.g. PDF download). */
export async function apiFetchBlob(
  path: string,
  init: Omit<RequestInit, "body"> & { auth?: boolean } = {},
): Promise<Blob> {
  const { auth = true, headers, ...rest } = init;
  const url = buildUrl(path);
  const mergedHeaders = new Headers(headers);
  if (auth) {
    const token = getAccessToken();
    if (token && !mergedHeaders.has("Authorization")) {
      mergedHeaders.set("Authorization", `Bearer ${token}`);
    }
  }
  const response = await fetch(url, {
    ...rest,
    method: rest.method ?? "GET",
    headers: mergedHeaders,
    cache: "no-store",
    credentials: "include",
  });
  if (!response.ok) {
    const contentType = response.headers.get("content-type") ?? "";
    const parsed = contentType.includes("application/json")
      ? await response.json().catch(() => null)
      : await response.text();
    const message = extractErrorMessage(parsed, response.statusText);
    throw new ApiError(message, response.status, parsed);
  }
  return response.blob();
}
