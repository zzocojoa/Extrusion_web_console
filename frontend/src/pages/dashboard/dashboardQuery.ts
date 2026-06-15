import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { fetchDashboard } from "../../api/dashboard";
import type { DashboardResponse } from "./dashboardTypes";

const useMockDashboard = import.meta.env.VITE_API_MODE !== "api";

async function getMockDashboard(language: string): Promise<DashboardResponse> {
  const { getLocalizedMockDashboard } = await import("./mockDashboardData");
  const state = new URLSearchParams(window.location.search).get("state");
  if (state === "ready" || state === "attention" || state === "blocked" || state === "running") {
    return getLocalizedMockDashboard(state, language);
  }
  return getLocalizedMockDashboard("running", language);
}

export function useDashboardQuery() {
  const { i18n } = useTranslation();

  return useQuery({
    queryKey: ["dashboard", i18n.language, window.location.search],
    queryFn: useMockDashboard ? () => getMockDashboard(i18n.language) : fetchDashboard,
    refetchInterval: 5000,
  });
}
