import axios from "axios";

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: "/api",
  timeout: 60000,
  headers: {
    "Content-Type": "application/json",
  },
});

export function getApiUrl(path: string) {
  return `${BASE}/api${path}`;
}

export interface ApiError {
  detail?: string;
  message?: string;
}

export async function fetchApi<T>(path: string, options?: RequestInit) {
  const response = await fetch(`/api${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error((body?.detail as string) || response.statusText);
  }
  return response.json() as Promise<T>;
}
