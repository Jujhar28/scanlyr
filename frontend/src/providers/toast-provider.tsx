"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { CheckCircle2, X, XCircle } from "lucide-react";

import { cn } from "@/lib/utils/cn";

export type ToastVariant = "success" | "error";

export type ToastInput = {
  title: string;
  description?: string;
  variant?: ToastVariant;
};

type ToastRecord = ToastInput & {
  id: string;
};

type ToastContextValue = {
  toast: (input: ToastInput) => void;
};

const ToastContext = createContext<ToastContextValue | null>(null);

const TOAST_DURATION_MS = 6000;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastRecord[]>([]);

  const dismiss = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const toast = useCallback(
    (input: ToastInput) => {
      const id =
        typeof crypto !== "undefined" && crypto.randomUUID
          ? crypto.randomUUID()
          : String(Date.now());
      const record: ToastRecord = { variant: "success", ...input, id };
      setToasts((prev) => [...prev, record]);
      window.setTimeout(() => dismiss(id), TOAST_DURATION_MS);
    },
    [dismiss],
  );

  const value = useMemo(() => ({ toast }), [toast]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div
        aria-live="polite"
        className="pointer-events-none fixed bottom-4 right-4 z-[100] flex w-full max-w-sm flex-col gap-2 p-4 sm:bottom-6 sm:right-6"
      >
        {toasts.map((t) => (
          <div
            key={t.id}
            role="status"
            className={cn(
              "pointer-events-auto flex gap-3 rounded-xl border px-4 py-3 shadow-lg backdrop-blur-sm",
              t.variant === "error"
                ? "border-red-500/40 bg-red-950/90 text-red-50"
                : "border-emerald-500/40 bg-emerald-950/90 text-emerald-50",
            )}
          >
            {t.variant === "error" ? (
              <XCircle className="mt-0.5 h-5 w-5 shrink-0" aria-hidden />
            ) : (
              <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0" aria-hidden />
            )}
            <div className="min-w-0 flex-1">
              <p className="text-sm font-semibold">{t.title}</p>
              {t.description ? (
                <p className="mt-0.5 text-xs opacity-90">{t.description}</p>
              ) : null}
            </div>
            <button
              type="button"
              className="shrink-0 rounded p-1 opacity-70 hover:opacity-100"
              aria-label="Dismiss notification"
              onClick={() => dismiss(t.id)}
            >
              <X className="h-4 w-4" aria-hidden />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    throw new Error("useToast must be used within ToastProvider");
  }
  return ctx;
}
