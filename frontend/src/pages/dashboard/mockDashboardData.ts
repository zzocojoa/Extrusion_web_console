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
      detail: "127.0.0.1:55321",
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
      detail: "별도 대시보드",
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
      detail: "127.0.0.1:55321",
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
      value: item.id === "upload" ? "대기" : item.value,
      detail: item.id === "upload" ? "미리보기 실행 가능" : item.detail,
    }));
    data.currentJob = null;
    data.recentJobs = data.recentJobs.map((job, index) => ({
      ...job,
      status: "succeeded",
      filesDone: job.filesTotal,
      failureCount: 0,
      warningCount: 0,
      latestMessage:
        index === 0
          ? "최근 업로드 완료, 현재 실행 중인 작업 없음"
          : "이전 작업 정상 완료",
    }));
    data.warningQueue = data.warningQueue.map((row) => ({
      ...row,
      tone: "ready",
      count: 0,
      impact: "확인 필요 항목 없음",
    }));
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
    data.recentJobs = [
      {
        ...data.recentJobs[1],
        jobId: "job_20260531_1745",
        status: "partial_failed",
        latestMessage: "일부 중복 3건과 TEMP 실패 2건 확인 필요",
      },
      data.recentJobs[2],
    ];
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
      value: item.id === "supabase" ? "연결 실패" : item.id === "upload" ? "차단됨" : item.value,
      detail:
        item.id === "supabase"
          ? "127.0.0.1:55321 연결 실패"
          : item.id === "upload"
            ? "Supabase 복구 필요"
            : item.detail,
    }));
    data.currentJob = null;
    data.runtimeChecks = data.runtimeChecks.map((row) =>
      row.id === "supabase"
        ? {
            ...row,
            tone: "blocked",
            detail: "127.0.0.1:55321 연결 실패",
          }
        : row.id === "edge_function"
          ? {
              ...row,
              tone: "blocked",
              detail: "Supabase 복구 후 확인 가능",
            }
          : row,
    );
    data.warningQueue = [
      {
        id: "supabase_unreachable",
        label: "Supabase 연결 실패",
        tone: "blocked",
        count: 1,
        impact: "업로드 시작 차단",
      },
      ...data.warningQueue.filter((row) => row.id !== "risky"),
    ];
    data.recentJobs = [
      {
        ...data.recentJobs[0],
        jobId: "job_20260601_0920",
        status: "interrupted",
        filesDone: 0,
        filesTotal: 18,
        rowsSent: 0,
        failureCount: 1,
        warningCount: 0,
        latestMessage: "Local Supabase 연결 실패로 업로드 차단",
      },
      data.recentJobs[1],
      data.recentJobs[2],
    ];
    data.auditSummary = [
      {
        auditId: "audit_blocked_001",
        time: "2026-06-01T09:20:00+09:00",
        result: "blocked",
        action: "upload.start",
        actor: "local\\operator",
        summary: "Local Supabase unreachable",
        jobId: "job_20260601_0920",
      },
      ...data.auditSummary,
    ];
  }

  return data;
}

export function getLocalizedMockDashboard(
  state: DashboardResponse["overall"]["state"],
  language: string,
): DashboardResponse {
  const data = getMockDashboardScenario(state);
  if (!language.startsWith("en")) {
    return data;
  }

  const byState: Record<DashboardResponse["overall"]["state"], Pick<DashboardResponse["overall"], "title" | "message">> = {
    ready: {
      title: "Upload ready",
      message: "Supabase, State Store, and WSL storage are ready. No blocking items found.",
    },
    attention: {
      title: "Needs attention",
      message: "There are 3 partial overlaps and 2 retryable failures. Check Upload Preview.",
    },
    blocked: {
      title: "Upload blocked",
      message: "Upload start is blocked because Local Supabase is not responding.",
    },
    running: {
      title: "Upload running",
      message: "Processing 12/18 files, 0 failures, average speed 24,000 rows/min.",
    },
  };

  data.overall.title = byState[state].title;
  data.overall.message = byState[state].message;
  data.topbarChips = data.topbarChips.map((chip) => ({
    ...chip,
    label: chip.id === "upload" ? "Upload" : chip.id === "state_store" ? "State Store" : chip.label,
    value:
      chip.value === "정상"
        ? "Ready"
        : chip.value === "실행 중"
          ? "Running"
          : chip.value === "연결됨"
            ? "Linked"
            : chip.value === "차단됨"
              ? "Blocked"
              : chip.value === "대기"
                ? "Idle"
                : chip.value === "확인 필요"
                  ? "Attention"
                  : chip.value,
  }));
  data.statusMatrix = data.statusMatrix.map((item) => ({
    ...item,
    label:
      item.id === "upload"
        ? "Upload"
        : item.id === "storage"
          ? "WSL Storage"
          : item.id === "state_store"
            ? "State Store"
            : item.label,
    value:
      item.value === "연결됨"
        ? "Linked"
        : item.value === "차단됨"
          ? "Blocked"
          : item.value === "대기"
            ? "Idle"
            : item.value === "연결 실패"
              ? "Unreachable"
          : item.value === "정상"
            ? "Ready"
            : item.value,
    detail:
      item.detail === "별도 대시보드"
        ? "External dashboard"
        : item.detail === "미리보기 실행 가능"
          ? "Preview available"
          : item.detail === "Docker / VHDX 정상"
            ? "Docker / VHDX healthy"
          : item.detail === "실패 재시도 2건"
            ? "2 retryable failures"
            : item.detail === "Supabase 복구 필요"
              ? "Restore Supabase first"
              : item.detail === "127.0.0.1:55321 연결 실패"
                ? "127.0.0.1:55321 unreachable"
                : item.detail,
    action: item.action ? { ...item.action, label: "Open Grafana" } : item.action,
  }));
  if (data.currentJob) {
    data.currentJob.latestMessage = "Uploading PLC data for 2026-06-01";
  }
  data.recentJobs = data.recentJobs.map((job) => ({
    ...job,
    latestMessage:
      job.status === "interrupted"
        ? "Upload blocked because Local Supabase is unreachable"
        : job.status === "partial_failed"
          ? "Review partial overlaps and 2 TEMP failures"
          : job.status === "succeeded"
            ? "Completed after excluding 1 partial overlap"
            : "Uploading PLC data for 2026-06-01",
  }));
  data.runtimeChecks = data.runtimeChecks.map((row) => ({
    ...row,
    label: row.id === "state_store" ? "State Store" : row.label,
    detail:
      row.detail === "127.0.0.1:55321 연결 실패"
        ? "127.0.0.1:55321 unreachable"
        : row.detail === "Supabase 복구 후 확인 가능"
          ? "Available after Supabase recovery"
          : row.detail,
  }));
  data.warningQueue = data.warningQueue.map((row) => ({
    ...row,
    label:
      row.id === "supabase_unreachable"
        ? "Supabase unreachable"
        : row.id === "partial_overlap"
          ? "Partial overlap"
          : row.id === "failed_retry"
            ? "Retry failed"
            : "Risk candidates",
    impact:
      row.id === "supabase_unreachable"
        ? "Upload start blocked"
        : row.count === 0
          ? "No items need attention"
          : row.id === "partial_overlap"
            ? "Check in Upload Preview"
            : "2 TEMP files can be retried",
  }));
  data.auditSummary = data.auditSummary.map((row) => ({
    ...row,
    summary:
      row.result === "blocked"
        ? "Local Supabase unreachable"
        : row.action === "upload.start"
          ? "18 targets, partial=false"
          : row.summary,
  }));
  return data;
}
