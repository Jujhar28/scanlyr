import type { Metadata } from "next";

import { SettingsPageClient } from "./settings-client";

export const metadata: Metadata = {
  title: "Organization",
};

export default function SettingsPage() {
  return <SettingsPageClient />;
}
