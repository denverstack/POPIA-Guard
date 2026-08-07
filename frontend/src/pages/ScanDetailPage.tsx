import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, ShieldOff, Download } from "lucide-react";
import { Layout } from "@/components/Layout";
import { StatusBadge } from "@/components/StatusBadge";
import { SeverityBadge } from "@/components/SeverityBadge";
import { RiskGauge } from "@/components/RiskGauge";
import { SeverityChart } from "@/components/SeverityChart";
import { EmptyState } from "@/components/EmptyState";
import { api, ApiError } from "@/lib/api";

export function ScanDetailPage() {
  const { scanId } = useParams<{ scanId: string }>();
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const [isDownloading, setIsDownloading] = useState(false);

  const scanQuery = useQuery({
    queryKey: ["scan", scanId],
    queryFn: () => api.getScan(scanId!),
    enabled: Boolean(scanId),
    // Poll while a scan is still running so the page updates without a manual refresh.
    refetchInterval: (query) =>
      query.state.data?.status === "running" || query.state.data?.status === "pending"
        ? 2000
        : false,
  });

  if (scanQuery.isLoading) {
    return (
      <Layout>
        <p className="text-sm text-text-secondary">Loading scan…</p>
      </Layout>
    );
  }

  if (scanQuery.isError || !scanQuery.data) {
    return (
      <Layout>
        <EmptyState
          icon={ShieldOff}
          title="Scan not found"
          description="This scan doesn't exist or you don't have access to it."
        >
          <Link to="/dashboard" className="text-sm font-medium text-accent hover:text-accent-hover">
            Back to scans
          </Link>
        </EmptyState>
      </Layout>
    );
  }

  const scan = scanQuery.data;

  async function handleDownload() {
    if (!scanId) return;
    setDownloadError(null);
    setIsDownloading(true);
    try {
      const { url } = await api.getScanReport(scanId);
      window.open(url, "_blank", "noopener,noreferrer");
    } catch (err) {
      setDownloadError(
        err instanceof ApiError && err.status === 404
          ? "No report is available for this scan yet."
          : "Couldn't get the report right now. Try again.",
      );
    } finally {
      setIsDownloading(false);
    }
  }

  return (
    <Layout>
      <Link
        to="/dashboard"
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-text-secondary hover:text-text-primary"
      >
        <ArrowLeft className="h-4 w-4" aria-hidden="true" />
        Back to scans
      </Link>

      <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="font-mono text-lg font-semibold text-text-primary">
            {scan.source_reference}
          </h1>
          <div className="mt-2 flex items-center gap-3">
            <StatusBadge status={scan.status} />
            <span className="text-sm text-text-secondary">{scan.files_scanned} files scanned</span>
          </div>
        </div>
        {scan.status === "completed" && (
          <div className="flex flex-col items-end gap-1.5">
            <button
              type="button"
              onClick={handleDownload}
              disabled={isDownloading}
              className="flex items-center gap-1.5 rounded-md border border-border-strong bg-card px-3 py-1.5 text-sm font-medium text-text-primary transition-colors hover:bg-surface-hover disabled:opacity-60"
            >
              <Download className="h-4 w-4" aria-hidden="true" />
              {isDownloading ? "Fetching…" : "Download report"}
            </button>
            {downloadError && (
              <p role="alert" className="text-xs text-critical">
                {downloadError}
              </p>
            )}
          </div>
        )}
      </div>

      {scan.status === "completed" && (
        <div className="mb-8 grid grid-cols-1 gap-6 rounded-lg border border-border bg-card p-6 sm:grid-cols-2">
          <div className="flex items-center justify-center">
            <RiskGauge
              compliancePercentage={scan.compliance_percentage}
              riskScore={scan.risk_score}
            />
          </div>
          <div>
            <h2 className="mb-3 text-sm font-medium text-text-primary">Findings by severity</h2>
            <SeverityChart findings={scan.findings} />
          </div>
        </div>
      )}

      {scan.status === "failed" && (
        <div className="mb-8 rounded-lg border border-critical-subtle bg-critical-subtle px-4 py-3 text-sm text-critical">
          This scan failed — the uploaded file may not have been a valid zip archive.
        </div>
      )}

      {(scan.status === "pending" || scan.status === "running") && (
        <div className="mb-8 rounded-lg border border-border bg-card px-4 py-3 text-sm text-text-secondary">
          Scan in progress — this page updates automatically.
        </div>
      )}

      {scan.status === "completed" && (
        <>
          <h2 className="mb-3 text-sm font-medium text-text-primary">
            Findings ({scan.findings.length})
          </h2>
          {scan.findings.length === 0 ? (
            <EmptyState
              icon={ShieldOff}
              title="No findings"
              description="This scan didn't detect any POPIA-sensitive data or secrets."
            />
          ) : (
            <div className="overflow-hidden rounded-lg border border-border bg-card">
              <table className="w-full text-left text-sm">
                <thead className="border-b border-border bg-surface text-xs uppercase tracking-wide text-text-secondary">
                  <tr>
                    <th scope="col" className="px-4 py-3 font-medium">
                      Severity
                    </th>
                    <th scope="col" className="px-4 py-3 font-medium">
                      Rule
                    </th>
                    <th scope="col" className="px-4 py-3 font-medium">
                      Location
                    </th>
                    <th scope="col" className="px-4 py-3 font-medium">
                      Match
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {scan.findings.map((finding) => (
                    <tr key={finding.id} className="border-b border-border last:border-0">
                      <td className="px-4 py-3">
                        <SeverityBadge severity={finding.severity} />
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-text-secondary">
                        {finding.rule_id}
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-text-primary">
                        {finding.file_path}:{finding.line_number}
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-text-secondary">
                        {finding.matched_snippet}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </Layout>
  );
}
