import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AI events",
};

export default function DetectionsLayout({ children }: { children: React.ReactNode }) {
  return children;
}
