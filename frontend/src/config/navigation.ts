import type { LucideIcon } from "lucide-react";
import {
  History,
  LayoutDashboard,
  Radar,
  ScanSearch,
  FileText,
  Plug,
  LineChart,
  User,
} from "lucide-react";

export type NavItem = {
  label: string;
  href: string;
  icon: LucideIcon;
};

/** Primary sidebar destinations under `/dashboard`. */
export const dashboardNav: NavItem[] = [
  { label: "Command center", href: "/dashboard", icon: LayoutDashboard },
  { label: "Security scan", href: "/dashboard/scan", icon: ScanSearch },
  { label: "History", href: "/dashboard/history", icon: History },
  { label: "AI events", href: "/dashboard/detections", icon: Radar },
  { label: "Risk analytics", href: "/dashboard/risk", icon: LineChart },
  { label: "Reports", href: "/dashboard/reports", icon: FileText },
  { label: "Integrations", href: "/dashboard/integrations", icon: Plug },
  { label: "Profile", href: "/dashboard/settings", icon: User },
];
