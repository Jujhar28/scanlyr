const ACCESS_KEY = "scanlyr.access_token";
const REFRESH_KEY = "scanlyr.refresh_token";

function canUseDom(): boolean {
  return typeof window !== "undefined" && typeof sessionStorage !== "undefined";
}

export function getAccessToken(): string | null {
  if (!canUseDom()) return null;
  return sessionStorage.getItem(ACCESS_KEY);
}

export function getRefreshToken(): string | null {
  if (!canUseDom()) return null;
  return sessionStorage.getItem(REFRESH_KEY);
}

export function setTokenPair(access: string, refresh: string): void {
  if (!canUseDom()) return;
  sessionStorage.setItem(ACCESS_KEY, access);
  sessionStorage.setItem(REFRESH_KEY, refresh);
}

export function clearTokenPair(): void {
  if (!canUseDom()) return;
  sessionStorage.removeItem(ACCESS_KEY);
  sessionStorage.removeItem(REFRESH_KEY);
}
