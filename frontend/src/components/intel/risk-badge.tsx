import { cn } from "@/lib/utils/cn";

type RiskLevel = "low" | "medium" | "high" | "critical";

const styles: Record<RiskLevel, string> = {
  low: "border-emerald-500/25 bg-emerald-50 text-emerald-700",
  medium: "border-amber-500/25 bg-amber-50 text-amber-800",
  high: "border-rose-500/25 bg-rose-50 text-rose-700",
  critical: "border-rose-600/30 bg-rose-100 text-rose-800",
};

export function RiskBadge({
  level,
  className,
}: {
  level: RiskLevel;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex rounded-full border px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wide",
        styles[level],
        className,
      )}
    >
      {level}
    </span>
  );
}
