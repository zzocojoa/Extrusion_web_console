import { useQuery } from "@tanstack/react-query";

import { fetchDashboard } from "../../api/dashboard";
import { getMockDashboardScenario, mockDashboardData } from "./mockDashboardData";
import type { DashboardResponse } from "./dashboardTypes";

const useMockDashboard = import.meta.env.VITE_API_MODE !== "api";

async function getMockDashboard(): Promise<DashboardResponse> {
  const state = new URLSearchParams(window.location.search).get("state");
  if (state === "ready" || state === "attention" || state === "blocked" || state === "running") {
    return getMockDashboardScenario(state);
  }
  return mockDashboardData;
}

export function useDashboardQuery() {
  return useQuery({
    queryKey: ["dashboard"],
    queryFn: useMockDashboard ? getMockDashboard : fetchDashboard,
    refetchInterval: 5000,
  });
}
