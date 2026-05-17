import { RequireAuth } from "@/components/auth/require-auth";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { ToastProvider } from "@/providers/toast-provider";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ToastProvider>
      <DashboardShell>
        <RequireAuth>{children}</RequireAuth>
      </DashboardShell>
    </ToastProvider>
  );
}