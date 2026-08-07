import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FolderSearch } from "lucide-react";
import { Layout } from "@/components/Layout";
import { StatusBadge } from "@/components/StatusBadge";
import { UploadDropzone } from "@/components/UploadDropzone";
import { EmptyState } from "@/components/EmptyState";
import { api, ApiError } from "@/lib/api";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export function DashboardPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [uploadError, setUploadError] = useState<string | null>(null);

  const scansQuery = useQuery({
    queryKey: ["scans"],
    queryFn: api.listScans,
  });

  const uploadMutation = useMutation({
    mutationFn: api.uploadScan,
    onSuccess: (result) => {
      setUploadError(null);
      queryClient.invalidateQueries({ queryKey: ["scans"] });
      navigate(`/scans/${result.id}`);
    },
    onError: (err) => {
      setUploadError(err instanceof ApiError ? err.message : "Upload failed. Try again.");
    },
  });

  return (
    <Layout>
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-text-primary">Scans</h1>
        <p className="mt-1 text-sm text-text-secondary">
          Upload a zip of a repository to check it for POPIA-sensitive data and leaked
          credentials.
        </p>
      </div>

      <div className="mb-8">
        <UploadDropzone
          onFileSelected={(file) => uploadMutation.mutate(file)}
          disabled={uploadMutation.isPending}
        />
        {uploadError && (
          <p role="alert" className="mt-2 text-sm text-critical">
            {uploadError}
          </p>
        )}
      </div>

      {scansQuery.isLoading && <p className="text-sm text-text-secondary">Loading scans…</p>}

      {scansQuery.isError && (
        <p role="alert" className="text-sm text-critical">
          Couldn't load your scans. Try refreshing the page.
        </p>
      )}

      {scansQuery.data && scansQuery.data.length === 0 && (
        <EmptyState
          icon={FolderSearch}
          title="No scans yet"
          description="Upload a zip file above to run your first scan."
        />
      )}

      {scansQuery.data && scansQuery.data.length > 0 && (
        <div className="overflow-hidden rounded-lg border border-border bg-card">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-border bg-surface text-xs uppercase tracking-wide text-text-secondary">
              <tr>
                <th scope="col" className="px-4 py-3 font-medium">
                  Source
                </th>
                <th scope="col" className="px-4 py-3 font-medium">
                  Status
                </th>
                <th scope="col" className="px-4 py-3 font-medium">
                  Files scanned
                </th>
                <th scope="col" className="px-4 py-3 font-medium">
                  Date
                </th>
              </tr>
            </thead>
            <tbody>
              {scansQuery.data.map((scan) => (
                <tr
                  key={scan.id}
                  onClick={() => navigate(`/scans/${scan.id}`)}
                  className="cursor-pointer border-b border-border last:border-0 hover:bg-surface-hover"
                >
                  <td className="px-4 py-3 font-mono text-xs text-text-primary">
                    {scan.source_reference}
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={scan.status} />
                  </td>
                  <td className="px-4 py-3 text-text-secondary">{scan.files_scanned}</td>
                  <td className="px-4 py-3 text-text-secondary">{formatDate(scan.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Layout>
  );
}
