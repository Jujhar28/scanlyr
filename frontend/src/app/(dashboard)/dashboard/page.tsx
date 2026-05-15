import type { Metadata } from "next";

import { OverviewDashboard } from "./overview-dashboard";

export const metadata: Metadata = {
  title: "Overview",
};

export default function DashboardHomePage() {
  return <OverviewDashboard />;
}
