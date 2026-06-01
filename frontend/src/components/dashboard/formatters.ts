import type { StatusTone, UploadJobStatus } from "../../pages/dashboard/dashboardTypes";

export function formatCount(value: number): string {
  return new Intl.NumberFormat().format(value);
}

export function formatKstTime(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export function statusToneForJob(status: UploadJobStatus): StatusTone {
  switch (status) {
    case "queued":
      return "muted";
    case "running":
      return "running";
    case "succeeded":
      return "ready";
    case "partial_failed":
    case "pausing":
    case "paused":
    case "cancelling":
    case "cancelled":
      return "attention";
    case "failed":
      return "failed";
    case "interrupted":
      return "blocked";
  }
}
