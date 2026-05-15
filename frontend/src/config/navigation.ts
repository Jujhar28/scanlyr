import type { LucideIcon } from "lucide-react";
import {
  LayoutDashboard,
  Radar,
  FileText,
  Settings2,
  Plug,
  LineChart,
} from "lucide-react";

export type NavItem = {
  label: string;
  href: string;
  icon: LucideIcon;
};

/** Primary sidebar destinations under `/dashboard`. */
export const dashboardNav: NavItem[] = [
  { label: "Overview", href: "/dashboard", icon: LayoutDashboard },
  { label: "AI events", href: "/dashboard/detections", icon: Radar },
  { label: "Risk & analytics", href: "/dashboard/risk", icon: LineChart },
  { label: "Reports", href: "/dashboard/reports", icon: FileText },
  { label: "Integrations", href: "/dashboard/integrations", icon: Plug },
  { label: "Organization", href: "/dashboard/settings", icon: Settings2 },
];
