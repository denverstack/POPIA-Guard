import type { Severity } from "@/types";

const LABELS: Record<Severity, string> = {
  critical: "Critical",
  high: "High",
  medium: "Medium",
  low: "Low",
};

const STYLES: Record<Severity, string> = {
  critical: "bg-critical-subtle text-critical",
  high: "bg-high-subtle text-high",
  medium: "bg-medium-subtle text-medium",
  low: "bg-low-subtle text-low",
};

export function SeverityBadge({ severity }: { severity: Severity }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${STYLES[severity]}`}
    >
      {LABELS[severity]}
    </span>
  );
}
