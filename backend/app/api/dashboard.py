from fastapi import APIRouter, Depends

from backend.app.core.settings import Settings, get_settings
from backend.app.schemas.dashboard import (
    AuditSummaryRow,
    CurrentJobSummary,
    DashboardLinkAction,
    DashboardOverall,
    DashboardResponse,
    RecentJobRow,
    RuntimeCheckRow,
    StatusMatrixItem,
    TopbarStatusChip,
    WarningQueueRow,
)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def build_mock_dashboard(settings: Settings) -> DashboardResponse:
    now = "2026-06-01T09:18:00+09:00"
    current_job_id = "job_20260601_0912"

    return DashboardResponse(
        overall=DashboardOverall(
            state="running",
            title="업로드 실행 중",
            message="현재 12/18 파일 처리, 실패 0, 평균 처리 속도 24,000 rows/min.",
            action="open_job",
        ),
        topbar_chips=[
            TopbarStatusChip(id="supabase", label="Supabase", tone="ready", value="정상"),
            TopbarStatusChip(id="upload", label="업로드", tone="running", value="실행 중"),
            TopbarStatusChip(id="grafana", label="Grafana", tone="ready", value="연결됨"),
            TopbarStatusChip(id="state_store", label="State Store", tone="ready", value="WAL"),
        ],
        status_matrix=[
            StatusMatrixItem(
                id="upload",
                label="업로드",
                tone="running",
                value="12/18 files",
                detail="실패 0 · ETA 4분",
            ),
            StatusMatrixItem(
                id="supabase",
                label="Local Supabase",
                tone="ready",
                value="DB + Edge OK",
                detail="127.0.0.1:55321",
            ),
            StatusMatrixItem(
                id="storage",
                label="WSL 저장소",
                tone="ready",
                value="126GB free",
                detail="Docker / VHDX 정상",
            ),
            StatusMatrixItem(
                id="grafana",
                label="Grafana",
                tone="ready",
                value="연결됨",
                detail="Open link only",
                action=DashboardLinkAction(
                    label="Grafana 열기",
                    href=settings.grafana_url,
                    target="_blank",
                ),
            ),
            StatusMatrixItem(
                id="state_store",
                label="State Store",
                tone="ready",
                value="WAL ready",
                detail="%APPDATA% state DB",
            ),
        ],
        current_job=CurrentJobSummary(
            job_id=current_job_id,
            status="running",
            progress_pct=67,
            files_done=12,
            files_total=18,
            rows_sent=182440,
            started_at="2026-06-01T09:12:00+09:00",
            latest_message="PLC 2026-06-01 데이터 업로드 중",
        ),
        recent_jobs=[
            RecentJobRow(
                job_id=current_job_id,
                status="running",
                started_at="2026-06-01T09:12:00+09:00",
                mode="upload",
                files_done=12,
                files_total=18,
                rows_sent=182440,
                failure_count=0,
                warning_count=0,
                latest_message="PLC 2026-06-01 데이터 업로드 중",
            ),
            RecentJobRow(
                job_id="job_20260531_1745",
                status="partial_failed",
                started_at="2026-05-31T17:45:00+09:00",
                mode="retry_failed",
                files_done=21,
                files_total=23,
                rows_sent=204118,
                failure_count=2,
                warning_count=3,
                latest_message="TEMP 파일 2개 재시도 필요",
            ),
            RecentJobRow(
                job_id="job_20260531_1010",
                status="succeeded",
                started_at="2026-05-31T10:10:00+09:00",
                mode="upload",
                files_done=16,
                files_total=16,
                rows_sent=166982,
                failure_count=0,
                warning_count=1,
                latest_message="부분 중복 1건 제외 후 완료",
            ),
        ],
        runtime_checks=[
            RuntimeCheckRow(
                id="supabase",
                label="Local Supabase",
                tone="ready",
                detail="127.0.0.1:55321",
                last_checked_at=now,
            ),
            RuntimeCheckRow(
                id="edge_function",
                label="Edge Function",
                tone="ready",
                detail="upload-metrics reachable",
                last_checked_at=now,
            ),
            RuntimeCheckRow(
                id="grafana",
                label="Grafana",
                tone="ready",
                detail=settings.grafana_url,
                last_checked_at=now,
                href=settings.grafana_url,
            ),
            RuntimeCheckRow(
                id="state_store",
                label="State Store",
                tone="ready",
                detail="web_console_state.db WAL mode",
                last_checked_at=now,
            ),
        ],
        warning_queue=[
            WarningQueueRow(
                id="partial_overlap",
                label="일부 중복",
                tone="attention",
                count=3,
                impact="Upload Preview에서 확인 필요",
            ),
            WarningQueueRow(
                id="failed_retry",
                label="실패 재시도",
                tone="attention",
                count=2,
                impact="TEMP 파일 2개 재시도 가능",
            ),
            WarningQueueRow(
                id="risky",
                label="위험 후보",
                tone="ready",
                count=0,
                impact="위험 후보 없음",
            ),
        ],
        audit_summary=[
            AuditSummaryRow(
                audit_id="audit_001",
                time="2026-06-01T09:15:00+09:00",
                result="success",
                action="upload.start",
                actor="local\\operator",
                summary="대상 18개, partial=false",
                job_id=current_job_id,
            ),
            AuditSummaryRow(
                audit_id="audit_002",
                time="2026-06-01T09:10:00+09:00",
                result="success",
                action="runtime.supabase.status",
                actor="system",
                summary="Local Supabase reachable",
            ),
        ],
    )


@router.get("", response_model=DashboardResponse)
def get_dashboard(settings: Settings = Depends(get_settings)) -> DashboardResponse:
    return build_mock_dashboard(settings)


@router.get("/summary", response_model=DashboardResponse)
def get_dashboard_summary(settings: Settings = Depends(get_settings)) -> DashboardResponse:
    return build_mock_dashboard(settings)
