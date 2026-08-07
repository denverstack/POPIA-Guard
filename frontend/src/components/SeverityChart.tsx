import { useMemo } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip,
  type ChartOptions,
} from "chart.js";
import { Bar } from "react-chartjs-2";
import type { Finding, Severity } from "@/types";

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip);

const SEVERITY_ORDER: Severity[] = ["critical", "high", "medium", "low"];
const SEVERITY_LABELS: Record<Severity, string> = {
  critical: "Critical",
  high: "High",
  medium: "Medium",
  low: "Low",
};
// Resolved hex values matching the CSS custom properties in index.css —
// Chart.js renders to canvas, so it can't read our Tailwind theme tokens
// directly.
const SEVERITY_COLORS: Record<Severity, string> = {
  critical: "#dc2626",
  high: "#ea580c",
  medium: "#d97706",
  low: "#64748b",
};

const CHART_OPTIONS: ChartOptions<"bar"> = {
  responsive: true,
  maintainAspectRatio: false,
  indexAxis: "y",
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: "#0f172a",
      padding: 8,
      titleFont: { family: "Inter", size: 12 },
      bodyFont: { family: "Inter", size: 12 },
    },
  },
  scales: {
    x: {
      beginAtZero: true,
      ticks: { precision: 0, font: { family: "Inter", size: 11 } },
      grid: { color: "#e2e8f0" },
    },
    y: {
      ticks: { font: { family: "Inter", size: 12 } },
      grid: { display: false },
    },
  },
};

export function SeverityChart({ findings }: { findings: Finding[] }) {
  const counts = useMemo(() => {
    const tally: Record<Severity, number> = { critical: 0, high: 0, medium: 0, low: 0 };
    for (const finding of findings) {
      tally[finding.severity] += 1;
    }
    return tally;
  }, [findings]);

  const data = {
    labels: SEVERITY_ORDER.map((s) => SEVERITY_LABELS[s]),
    datasets: [
      {
        data: SEVERITY_ORDER.map((s) => counts[s]),
        backgroundColor: SEVERITY_ORDER.map((s) => SEVERITY_COLORS[s]),
        borderRadius: 4,
        barThickness: 20,
      },
    ],
  };

  return (
    <div className="h-48">
      <Bar data={data} options={CHART_OPTIONS} />
    </div>
  );
}
