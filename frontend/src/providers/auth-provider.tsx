"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { usePathname, useRouter } from "next/navigation";

import { apiFetch } from "@/lib/api/client";
import type { AuthOrganization, AuthSession, AuthUser } from "@/lib/auth/types";
import {
  clearTokenPair,
  getAccessToken,
  getRefreshToken,
  setTokenPair,
} from "@/lib/auth/token-store";

type AuthContextValue = {
  user: AuthUser | null;
  organization: AuthOrganization | null;
  role: string | null;
  hydrated: boolean;
  signInWithSession: (session: AuthSession) => void;
  signOut: () => Promise<void>;
  refreshSession: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

async function postJson<T>(path: string, json: unknown): Promise<T> {
  return apiFetch<T>(path, { method: "POST", json });
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();

  const [user, setUser] = useState<AuthUser | null>(null);
  const [organization, setOrganization] = useState<AuthOrganization | null>(null);
  const [role, setRole] = useState<string | null>(null);
  const [hydrated, setHydrated] = useState(false);

  const applySession = useCallback((session: AuthSession) => {
    setTokenPair(session.tokens.access_token, session.tokens.refresh_token);
    setUser(session.user);
    setOrganization(session.organization);
    setRole(session.role);
  }, []);

  const refreshSession = useCallback(async () => {
    const refresh = getRefreshToken();
    if (!refresh) {
      clearTokenPair();
      setUser(null);
      setOrganization(null);
      setRole(null);
      return;
    }
    const session = await postJson<AuthSession>("auth/refresh", {
      refresh_token: refresh,
    });
    applySession(session);
  }, [applySession]);

  useEffect(() => {
    let cancelled = false;

    async function bootstrap() {
      const access = getAccessToken();
      const refresh = getRefreshToken();

      if (!access && refresh) {
        try {
          await refreshSession();
        } catch {
          clearTokenPair();
        }
        if (!cancelled) setHydrated(true);
        return;
      }

      if (!access) {
        if (!cancelled) setHydrated(true);
        return;
      }

      try {
        const me = await apiFetch<{
          user: AuthUser;
          organization: AuthOrganization;
          role: string;
        }>("auth/me");
        if (cancelled) return;
        setUser(me.user);
        setOrganization(me.organization);
        setRole(me.role);
      } catch {
        try {
          await refreshSession();
        } catch {
          clearTokenPair();
          if (!cancelled) {
            setUser(null);
            setOrganization(null);
            setRole(null);
          }
        }
      } finally {
        if (!cancelled) setHydrated(true);
      }
    }

    void bootstrap();
    return () => {
      cancelled = true;
    };
  }, [refreshSession]);

  const signInWithSession = useCallback(
    (session: AuthSession) => {
      applySession(session);
      if (pathname?.startsWith("/login") || pathname?.startsWith("/register")) {
        router.replace("/dashboard");
      }
    },
    [applySession, pathname, router],
  );

  const signOut = useCallback(async () => {
    const access = getAccessToken();
    try {
      if (access) {
        await postJson("auth/logout", { revoke_all: true });
      }
    } catch {
      // best-effort
    }
    clearTokenPair();
    setUser(null);
    setOrganization(null);
    setRole(null);
    router.replace("/login");
  }, [router]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      organization,
      role,
      hydrated,
      signInWithSession,
      signOut,
      refreshSession,
    }),
    [hydrated, organization, refreshSession, role, signInWithSession, signOut, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
