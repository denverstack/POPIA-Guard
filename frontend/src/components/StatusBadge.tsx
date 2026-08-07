import type { ScanStatus } from "@/types";

const LABELS: Record<ScanStatus, string> = {
  pending: "Pending",
  running: "Running",
  completed: "Completed",
  failed: "Failed",
};

const STYLES: Record<ScanStatus, string> = {
  pending: "bg-low-subtle text-low",
  running: "bg-accent-subtle text-accent",
  completed: "bg-success-subtle text-success",
  failed: "bg-critical-subtle text-critical",
};

export function StatusBadge({ status }: { status: ScanStatus }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium ${STYLES[status]}`}
    >
      {status === "running" && (
        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-current" aria-hidden="true" />
      )}
      {LABELS[status]}
    </span>
  );
}
