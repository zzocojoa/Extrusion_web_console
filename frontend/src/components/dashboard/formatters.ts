import type { StatusTone, UploadJobStatus } from "../../pages/dashboard/dashboardTypes";

function localeFromLanguage(language: string): string {
  return language.startsWith("en") ? "en-US" : "ko-KR";
}

export function formatCount(value: number, language = "ko"): string {
  return new Intl.NumberFormat(localeFromLanguage(language)).format(value);
}

export function formatKstTime(value: string, language = "ko"): string {
  return new Intl.DateTimeFormat(localeFromLanguage(language), {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "Asia/Seoul",
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
      return "attention";
    case "cancelled":
      return "muted";
    case "failed":
      return "failed";
    case "interrupted":
      return "blocked";
  }
}
