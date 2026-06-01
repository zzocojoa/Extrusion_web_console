import type { DashboardResponse } from "./dashboardTypes";

export const mockDashboardData: DashboardResponse = {
  overall: {
    state: "running",
    title: "업로드 실행 중",
    message: "현재 12/18 파일 처리, 실패 0, 평균 처리 속도 24,000 rows/min.",
    action: "open_job",
  },
  topbarChips: [
    { id: "supabase", label: "Supabase", tone: "ready", value: "정상" },
    { id: "upload", label: "업로드", tone: "running", value: "실행 중" },
    { id: "grafana", label: "Grafana", tone: "ready", value: "연결됨" },
    { id: "state_store", label: "State Store", tone: "ready", value: "WAL" },
  ],
  statusMatrix: [
    {
      id: "upload",
      label: "업로드",
      tone: "running",
      value: "12/18 files",
      detail: "실패 0 · ETA 4분",
    },
    {
      id: "supabase",
      label: "Local Supabase",
      tone: "ready",
      value: "DB + Edge OK",
      detail: "127.0.0.1:54321",
    },
    {
      id: "storage",
      label: "WSL 저장소",
      tone: "ready",
      value: "126GB free",
      detail: "Docker / VHDX 정상",
    },
    {
      id: "grafana",
      label: "Grafana",
      tone: "ready",
      value: "연결됨",
      detail: "Open link only",
      action: { label: "Grafana 열기", href: "http://localhost:3001", target: "_blank" },
    },
    {
      id: "state_store",
      label: "State Store",
      tone: "ready",
      value: "WAL ready",
      detail: "%APPDATA% state DB",
    },
  ],
  currentJob: {
    jobId: "job_20260601_0912",
    status: "running",
    progressPct: 67,
    filesDone: 12,
    filesTotal: 18,
    rowsSent: 182440,
    startedAt: "2026-06-01T09:12:00+09:00",
    latestMessage: "PLC 2026-06-01 데이터 업로드 중",
  },
  recentJobs: [
    {
      jobId: "job_20260601_0912",
      status: "running",
      startedAt: "2026-06-01T09:12:00+09:00",
      mode: "upload",
      filesDone: 12,
      filesTotal: 18,
      rowsSent: 182440,
      failureCount: 0,
      warningCount: 0,
      latestMessage: "PLC 2026-06-01 데이터 업로드 중",
    },
    {
      jobId: "job_20260531_1745",
      status: "partial_failed",
      startedAt: "2026-05-31T17:45:00+09:00",
      mode: "retry_failed",
      filesDone: 21,
      filesTotal: 23,
      rowsSent: 204118,
      failureCount: 2,
      warningCount: 3,
      latestMessage: "TEMP 파일 2개 재시도 필요",
    },
    {
      jobId: "job_20260531_1010",
      status: "succeeded",
      startedAt: "2026-05-31T10:10:00+09:00",
      mode: "upload",
      filesDone: 16,
      filesTotal: 16,
      rowsSent: 166982,
      failureCount: 0,
      warningCount: 1,
      latestMessage: "부분 중복 1건 제외 후 완료",
    },
  ],
  runtimeChecks: [
    {
      id: "supabase",
      label: "Local Supabase",
      tone: "ready",
      detail: "127.0.0.1:54321",
      lastCheckedAt: "2026-06-01T09:18:00+09:00",
    },
    {
      id: "edge_function",
      label: "Edge Function",
      tone: "ready",
      detail: "upload-metrics reachable",
      lastCheckedAt: "2026-06-01T09:18:00+09:00",
    },
    {
      id: "grafana",
      label: "Grafana",
      tone: "ready",
      detail: "http://localhost:3001",
      lastCheckedAt: "2026-06-01T09:18:00+09:00",
      href: "http://localhost:3001",
    },
    {
      id: "state_store",
      label: "State Store",
      tone: "ready",
      detail: "web_console_state.db WAL mode",
      lastCheckedAt: "2026-06-01T09:18:00+09:00",
    },
  ],
  warningQueue: [
    {
      id: "partial_overlap",
      label: "일부 중복",
      tone: "attention",
      count: 3,
      impact: "Upload Preview에서 확인 필요",
    },
    {
      id: "failed_retry",
      label: "실패 재시도",
      tone: "attention",
      count: 2,
      impact: "TEMP 파일 2개 재시도 가능",
    },
    {
      id: "risky",
      label: "위험 후보",
      tone: "ready",
      count: 0,
      impact: "위험 후보 없음",
    },
  ],
  auditSummary: [
    {
      auditId: "audit_001",
      time: "2026-06-01T09:15:00+09:00",
      result: "success",
      action: "upload.start",
      actor: "local\\operator",
      summary: "대상 18개, partial=false",
      jobId: "job_20260601_0912",
    },
    {
      auditId: "audit_002",
      time: "2026-06-01T09:10:00+09:00",
      result: "success",
      action: "runtime.supabase.status",
      actor: "system",
      summary: "Local Supabase reachable",
    },
  ],
};

function cloneDashboard(data: DashboardResponse): DashboardResponse {
  return JSON.parse(JSON.stringify(data)) as DashboardResponse;
}

export function getMockDashboardScenario(state: DashboardResponse["overall"]["state"]): DashboardResponse {
  const data = cloneDashboard(mockDashboardData);
  data.overall.state = state;

  if (state === "ready") {
    data.overall.title = "업로드 준비됨";
    data.overall.message = "Supabase, State Store, WSL 저장소가 정상이며 차단 항목이 없습니다.";
    data.overall.action = "preview";
    data.topbarChips = data.topbarChips.map((chip) => ({
      ...chip,
      tone: chip.id === "upload" ? "ready" : chip.tone,
      value: chip.id === "upload" ? "대기" : chip.value,
    }));
    data.statusMatrix = data.statusMatrix.map((item) => ({
      ...item,
      tone: item.id === "upload" ? "ready" : item.tone,
      value: item.id === "upload" ? "ready" : item.value,
      detail: item.id === "upload" ? "미리보기 실행 가능" : item.detail,
    }));
    data.currentJob = null;
    return data;
  }

  if (state === "attention") {
    data.overall.title = "확인 필요";
    data.overall.message = "일부 중복 3건과 재시도 가능한 실패 2건이 있습니다. Upload Preview에서 확인하세요.";
    data.overall.action = "preview";
    data.topbarChips = data.topbarChips.map((chip) => ({
      ...chip,
      tone: chip.id === "upload" ? "attention" : chip.tone,
      value: chip.id === "upload" ? "확인 필요" : chip.value,
    }));
    data.statusMatrix = data.statusMatrix.map((item) => ({
      ...item,
      tone: item.id === "upload" ? "attention" : item.tone,
      value: item.id === "upload" ? "partial 3" : item.value,
      detail: item.id === "upload" ? "실패 재시도 2건" : item.detail,
    }));
    data.currentJob = null;
    return data;
  }

  if (state === "blocked") {
    data.overall.title = "업로드 차단됨";
    data.overall.message = "Local Supabase가 응답하지 않아 업로드 시작을 차단했습니다.";
    data.overall.action = "open_logs";
    data.topbarChips = data.topbarChips.map((chip) => ({
      ...chip,
      tone: chip.id === "supabase" ? "blocked" : chip.id === "upload" ? "blocked" : chip.tone,
      value: chip.id === "supabase" ? "차단됨" : chip.id === "upload" ? "차단됨" : chip.value,
    }));
    data.statusMatrix = data.statusMatrix.map((item) => ({
      ...item,
      tone: item.id === "supabase" || item.id === "upload" ? "blocked" : item.tone,
      value: item.id === "supabase" ? "unreachable" : item.id === "upload" ? "blocked" : item.value,
      detail:
        item.id === "supabase"
          ? "127.0.0.1:54321 연결 실패"
          : item.id === "upload"
            ? "Supabase 복구 필요"
            : item.detail,
    }));
    data.currentJob = null;
  }

  return data;
}
