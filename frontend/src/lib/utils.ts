import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(value: string | number, currency = "USD") {
  const num = typeof value === "string" ? parseFloat(value) || 0 : value || 0;
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(num);
}

export function formatPercent(value: string | number) {
  const num = typeof value === "string" ? parseFloat(value) || 0 : value || 0;
  return `${num.toFixed(1)}%`;
}

export function formatNumber(value: string | number) {
  const num = typeof value === "string" ? parseFloat(value) || 0 : value || 0;
  return new Intl.NumberFormat("en-US").format(num);
}

export function statusColor(status: string) {
  const map: Record<string, string> = {
    verified: "emerald",
    needs_review: "amber",
    unverified: "gray",
    unavailable: "gray",
    configuration_required: "amber",
    supported: "emerald",
    unsupported: "risk",
    suitable: "emerald",
    likely_unsuitable: "risk",
    strong: "emerald",
    moderate: "amber",
    weak: "risk",
    low: "emerald",
    medium: "amber",
    high: "risk",
    unknown: "gray",
    insufficient_evidence: "gray",
    stable: "emerald",
    volatile: "risk",
    promising_test_required: "electric",
    strong_candidate: "emerald",
    monitor: "amber",
    high_risk: "risk",
    reject: "risk",
    emerging: "electric",
    growing: "emerald",
    declining: "risk",
    saturated: "risk",
    established: "emerald",
  };
  return map[status] || "navy";
}

export function statusLabel(status: string) {
  const map: Record<string, string> = {
    verified: "Verified",
    needs_review: "Needs review",
    unverified: "Unverified",
    unavailable: "Unavailable",
    configuration_required: "Configuration required",
    supported: "Supported",
    unsupported: "Unsupported",
    suitable: "Suitable",
    likely_unsuitable: "Likely unsuitable",
    strong: "Strong",
    moderate: "Moderate",
    weak: "Weak",
    low: "Low",
    medium: "Medium",
    high: "High",
    unknown: "Unknown",
    insufficient_evidence: "Insufficient evidence",
    stable: "Stable",
    volatile: "Volatile",
    promising_test_required: "Promising — test required",
    strong_candidate: "Strong candidate",
    monitor: "Monitor",
    high_risk: "High risk",
    reject: "Reject",
    emerging: "Emerging",
    growing: "Growing",
    declining: "Declining",
    saturated: "Saturated",
    established: "Established",
  };
  return map[status] || status;
}
