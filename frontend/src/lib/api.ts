import type { ScanJob, ScanResult, Finding, User } from "@/types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";
const TOKEN_STORAGE_KEY = "popia_guard_token";

interface ReportUrl {
  url: string;
  expires_in: number;
}

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_STORAGE_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_STORAGE_KEY);
}

interface RequestOptions {
  method?: string;
  body?: BodyInit;
  headers?: Record<string, string>;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = { ...options.headers };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: options.method ?? "GET",
    body: options.body,
    headers,
  });

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const body = await response.json();
      if (body?.detail) message = body.detail;
    } catch {
      // response wasn't JSON — keep the generic message
    }
    throw new ApiError(message, response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export const api = {
  register(input: { email: string; password: string; full_name: string }): Promise<User> {
    return request<User>("/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
    });
  },

  async login(input: { email: string; password: string }): Promise<void> {
    const { access_token } = await request<{ access_token: string; token_type: string }>(
      "/auth/login",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(input),
      },
    );
    setToken(access_token);
  },

  listScans(): Promise<ScanJob[]> {
    return request<ScanJob[]>("/scans");
  },

  getScan(scanId: string): Promise<ScanResult> {
    return request<ScanResult>(`/scans/${scanId}`);
  },

  getScanFindings(scanId: string): Promise<Finding[]> {
    return request<Finding[]>(`/scans/${scanId}/findings`);
  },

  getScanReport(scanId: string): Promise<ReportUrl> {
    return request<ReportUrl>(`/scans/${scanId}/report`);
  },

  uploadScan(file: File): Promise<ScanResult> {
    const formData = new FormData();
    formData.append("file", file);
    return request<ScanResult>("/scans", {
      method: "POST",
      body: formData,
    });
  },
};
