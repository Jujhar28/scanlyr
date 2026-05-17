import type { Metadata } from "next";

import { ScanWorkspace } from "@/components/scan/scan-workspace";

export const metadata: Metadata = {
  title: "Security scan",
};

export default function ScanPage() {
  return <ScanWorkspace />;
}
