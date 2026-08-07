// Mirrors backend/app/schemas/*.py — keep these in sync with the API.

export type Severity = "critical" | "high" | "medium" | "low";
export type FindingCategory = "popia" | "secret";
export type ScanStatus = "pending" | "running" | "completed" | "failed";
export type SourceType = "upload" | "github";

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
}

export interface Finding {
  id: string;
  category: FindingCategory;
  rule_id: string;
  severity: Severity;
  file_path: string;
  line_number: number;
  matched_snippet: string;
  created_at: string;
}

export interface ScanJob {
  id: string;
  source_type: SourceType;
  source_reference: string;
  status: ScanStatus;
  files_scanned: number;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface ScanResult extends ScanJob {
  findings: Finding[];
  risk_score: number;
  compliance_percentage: number;
}

export interface ApiErrorBody {
  detail: string;
}
