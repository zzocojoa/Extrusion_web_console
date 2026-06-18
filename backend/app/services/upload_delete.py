from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Protocol
from urllib.parse import urlparse
from uuid import uuid4

import sqlite3

from backend.app.core.settings import Settings
from backend.app.core.target_class import classify_database_url
from backend.app.db.audit_repository import AuditRepository
from backend.app.db.preview_repository import iso_now
from backend.app.db.upload_delete_repository import UploadDeleteRepository
from backend.app.schemas.audit import AuditResult
from backend.app.schemas.upload_delete import (
    DeleteDbTargetGuard,
    DeleteJobCreateRequest,
    DeleteJobCreateResponse,
    DeletePreflightRequest,
    DeletePreflightResponse,
    DeletePreflightStatus,
    DeleteReconcileResponse,
    DeleteRunStatus,
)
from backend.app.services.upload_preview import (
    CandidateFile,
    CsvKeyExtractor,
    KeyExtractionResult,
    SourceFolder,
    build_file_signature,
)


PREFLIGHT_TTL_SECONDS = 15 * 60
PREVIEW_FRESHNESS_MAX_AGE_SECONDS = 24 * 60 * 60
MAX_DELETE_KEYS = 100_000
POSTGRES_CONTAINER_PORT = 5432


class DeleteRejectedError(RuntimeError):
    def __init__(self, reason: str, *, status_code: int = 422, detail: dict | None = None) -> None:
        super().__init__(reason)
        self.reason = reason
        self.status_code = status_code
        self.detail = detail or {}


class DeleteDbBlockedError(RuntimeError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class DeleteDbFailedError(RuntimeError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class DeleteCommitUnknownError(RuntimeError):
    pass


@dataclass(frozen=True)
class DbGuardResult:
    passed: bool
    target_class: str
    fingerprint_hash: str | None
    reason_code: str | None = None

    def to_api(self) -> DeleteDbTargetGuard:
        return DeleteDbTargetGuard(
            status="passed" if self.passed else "blocked",
            target_class=self.target_class,
            fingerprint_hash=self.fingerprint_hash,
            reason_code=self.reason_code,
        )


class DeleteDbClient(Protocol):
    def target_guard(self) -> DbGuardResult:
        ...

    def guard(self) -> DbGuardResult:
        ...

    def count_existing_keys(self, keys: set[tuple[str, str]]) -> int:
        ...

    def delete_keys(self, keys: set[tuple[str, str]], *, expected_count: int) -> int:
        ...


@dataclass(frozen=True)
class KeyEvidence:
    keys: set[tuple[str, str]]
    selected_item_ids: list[int]
    selected_item_count: int
    selected_key_count: int
    selection_hash: str
    keyset_hash: str
    rollback_ready: bool
    rollback_blockers: list[str]
    items: list[sqlite3.Row]
    timestamp_start_date: date | None = None
    timestamp_end_date: date | None = None


class PsycopgDeleteDbClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def target_guard(self) -> DbGuardResult:
        return self._guard(require_delete_privilege=False)

    def guard(self) -> DbGuardResult:
        return self._guard(require_delete_privilege=True)

    def _guard(self, *, require_delete_privilege: bool) -> DbGuardResult:
        classified = classify_database_url(
            self.settings.supabase_db_url,
            expected_db_port=self.settings.local_supabase_db_port,
            source="supabase_db_url" if self.settings.supabase_db_url else "not_configured",
        )
        if not classified.configured:
            return DbGuardResult(False, classified.target_class, None, "db_url_missing")
        if classified.target_class != "loopback_expected_db_port":
            return DbGuardResult(False, classified.target_class, None, "db_target_not_local")
        try:
            import psycopg  # type: ignore[import-not-found]
        except Exception:
            return DbGuardResult(False, classified.target_class, None, "psycopg_unavailable")
        try:
            with psycopg.connect(self.settings.supabase_db_url, autocommit=True, connect_timeout=5) as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT inet_server_port(), current_database(), current_user")
                    port, database_name, _user = cursor.fetchone()
                    if not self._server_port_matches_expected(int(port)):
                        return DbGuardResult(False, classified.target_class, None, "db_port_mismatch")
                    cursor.execute("SELECT to_regclass('public.all_metrics') IS NOT NULL")
                    if cursor.fetchone()[0] is not True:
                        return DbGuardResult(False, classified.target_class, None, "all_metrics_missing")
                    cursor.execute(
                        """
                        SELECT COUNT(*) > 0
                        FROM pg_indexes
                        WHERE schemaname = 'public'
                          AND tablename = 'all_metrics'
                          AND indexdef ILIKE '%UNIQUE%'
                          AND indexdef ILIKE '%timestamp%'
                          AND indexdef ILIKE '%device_id%'
                        """
                    )
                    if cursor.fetchone()[0] is not True:
                        return DbGuardResult(False, classified.target_class, None, "all_metrics_unique_key_missing")
                    if require_delete_privilege:
                        cursor.execute("SELECT has_table_privilege(current_user, 'public.all_metrics', 'DELETE')")
                        if cursor.fetchone()[0] is not True:
                            return DbGuardResult(False, classified.target_class, None, "db_delete_permission_denied")
                    fingerprint_hash = safe_hash(
                        {
                            "hostClass": classified.host_class,
                            "portClass": classified.port_class,
                            "databaseNameClass": classify_database_name(str(database_name)),
                            "schemaSignature": "public.all_metrics.timestamp_device_id_unique",
                            "runtimeProjectClass": classify_project_id(self.settings.local_supabase_project_id),
                        }
                    )
                    return DbGuardResult(True, classified.target_class, fingerprint_hash)
        except Exception:
            return DbGuardResult(False, classified.target_class, None, "db_guard_unreachable")

    def _server_port_matches_expected(self, server_port: int) -> bool:
        expected_port = int(self.settings.local_supabase_db_port)
        if server_port == expected_port:
            return True
        return server_port == POSTGRES_CONTAINER_PORT and expected_port != POSTGRES_CONTAINER_PORT

    def count_existing_keys(self, keys: set[tuple[str, str]]) -> int:
        if not keys:
            return 0
        try:
            import psycopg  # type: ignore[import-not-found]
        except Exception as error:
            raise DeleteDbBlockedError("psycopg_unavailable") from error
        payload = json.dumps(
            [{"timestamp": timestamp, "device_id": device_id} for timestamp, device_id in sorted(keys)],
            ensure_ascii=False,
            separators=(",", ":"),
        )
        with psycopg.connect(self.settings.supabase_db_url, autocommit=True, connect_timeout=5) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    WITH delete_key_stage AS (
                      SELECT DISTINCT s."timestamp", s.device_id
                      FROM jsonb_to_recordset(%s::jsonb) AS s("timestamp" timestamptz, device_id text)
                    )
                    SELECT COUNT(*) AS count
                    FROM delete_key_stage s
                    JOIN public.all_metrics m
                      ON m."timestamp" = s.timestamp
                     AND m.device_id = s.device_id
                    """,
                    (payload,),
                )
                return int(cursor.fetchone()[0])

    def delete_keys(self, keys: set[tuple[str, str]], *, expected_count: int) -> int:
        if not keys:
            return 0
        try:
            import psycopg  # type: ignore[import-not-found]
        except Exception as error:
            raise DeleteDbBlockedError("psycopg_unavailable") from error
        try:
            with psycopg.connect(self.settings.supabase_db_url, autocommit=False, connect_timeout=5) as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", ("30000",))
                    cursor.execute("SELECT pg_advisory_xact_lock(hashtext('ewc_upload_delete_already_in_db_v1'))")
                    cursor.execute("SELECT has_table_privilege(current_user, 'public.all_metrics', 'DELETE')")
                    if cursor.fetchone()[0] is not True:
                        raise DeleteDbBlockedError("db_delete_permission_denied")
                    self._stage_keys(cursor, keys)
                    cursor.execute(
                        """
                        SELECT COUNT(*) AS count
                        FROM delete_key_stage s
                        JOIN public.all_metrics m
                          ON m."timestamp" = s.timestamp
                         AND m.device_id = s.device_id
                        """
                    )
                    matched = int(cursor.fetchone()[0])
                    if matched != expected_count:
                        raise DeleteDbBlockedError("db_key_count_mismatch")
                    cursor.execute(
                        """
                        DELETE FROM public.all_metrics m
                        USING delete_key_stage s
                        WHERE m."timestamp" = s.timestamp
                          AND m.device_id = s.device_id
                        RETURNING 1
                        """
                    )
                    deleted = len(cursor.fetchall())
                    if deleted != expected_count:
                        raise DeleteDbFailedError("deleted_count_mismatch")
                try:
                    connection.commit()
                except Exception as error:
                    raise DeleteCommitUnknownError() from error
                return deleted
        except (DeleteDbBlockedError, DeleteDbFailedError, DeleteCommitUnknownError):
            raise
        except Exception as error:
            raise DeleteDbFailedError("delete_transaction_failed") from error

    def _stage_keys(self, cursor, keys: set[tuple[str, str]]) -> None:
        cursor.execute(
            """
            CREATE TEMP TABLE delete_key_stage (
              timestamp timestamptz NOT NULL,
              device_id text NOT NULL,
              PRIMARY KEY(timestamp, device_id)
            ) ON COMMIT DROP
            """
        )
        sorted_keys = sorted(keys)
        for index in range(0, len(sorted_keys), 5000):
            cursor.executemany(
                """
                INSERT INTO delete_key_stage(timestamp, device_id)
                VALUES (%s::timestamptz, %s::text)
                ON CONFLICT DO NOTHING
                """,
                sorted_keys[index : index + 5000],
            )


class UploadDeleteService:
    def __init__(
        self,
        *,
        settings: Settings,
        repository: UploadDeleteRepository,
        audit_repository: AuditRepository,
        db_client: DeleteDbClient | None = None,
        runtime_ready: Callable[[], tuple[bool, str | None]] | None = None,
    ) -> None:
        self.settings = settings
        self.repository = repository
        self.audit_repository = audit_repository
        self.db_client = db_client or PsycopgDeleteDbClient(settings)
        self.extractor = CsvKeyExtractor()
        self.runtime_ready = runtime_ready or (lambda: default_runtime_ready(settings))

    def create_preflight(self, request: DeletePreflightRequest) -> DeletePreflightResponse:
        preflight_id = f"dpf_{uuid4().hex[:12]}"
        selected_ids = sorted(set(request.preview_item_ids))
        if len(selected_ids) != len(request.preview_item_ids):
            return self._blocked_preflight(preflight_id, request, "selection_duplicate_item")
        if request.expected_already_in_db_items != len(selected_ids):
            return self._blocked_preflight(preflight_id, request, "expected_selection_count_mismatch")
        blocker = self._common_start_blocker()
        if blocker:
            return self._blocked_preflight(preflight_id, request, blocker)
        runtime_ok, runtime_reason = self.runtime_ready()
        if not runtime_ok:
            return self._blocked_preflight(preflight_id, request, runtime_reason or "runtime_not_ready")
        preview = self.repository.get_preview_run(request.preview_run_id)
        preview_blocker = self._preview_blocker(preview, request.preview_run_id)
        if preview_blocker:
            return self._blocked_preflight(preflight_id, request, preview_blocker)
        assert preview is not None
        items = self.repository.get_preview_items(request.preview_run_id, selected_ids)
        if len(items) != len(selected_ids):
            return self._blocked_preflight(preflight_id, request, "selection_item_missing")
        if any(str(item["status"]) != "already_in_db" for item in items):
            return self._blocked_preflight(preflight_id, request, "selection_contains_non_already_in_db")
        timestamp_scope = timestamp_scope_from_request(request)
        evidence = self._build_key_evidence(items, timestamp_scope=timestamp_scope)
        if evidence.selected_key_count <= 0:
            return self._blocked_preflight(preflight_id, request, "delete_selection_empty", evidence=evidence)
        if evidence.selected_key_count > MAX_DELETE_KEYS:
            return self._blocked_preflight(preflight_id, request, "delete_selection_too_large", evidence=evidence)
        if not evidence.rollback_ready:
            return self._blocked_preflight(
                preflight_id,
                request,
                "rollback_not_ready",
                evidence=evidence,
                rollback_blockers=evidence.rollback_blockers,
            )
        guard = self.db_client.guard()
        if not guard.passed:
            return self._blocked_preflight(preflight_id, request, guard.reason_code or "db_target_guard_failed", evidence=evidence, guard=guard)
        try:
            db_count = self.db_client.count_existing_keys(evidence.keys)
        except DeleteDbBlockedError as error:
            return self._blocked_preflight(preflight_id, request, error.reason, evidence=evidence, guard=guard)
        except Exception:
            return self._blocked_preflight(preflight_id, request, "db_count_check_failed", evidence=evidence, guard=guard)
        if db_count != evidence.selected_key_count:
            return self._blocked_preflight(preflight_id, request, "db_key_count_mismatch", evidence=evidence, guard=guard)
        expires_at = utc_now() + timedelta(seconds=PREFLIGHT_TTL_SECONDS)
        self.repository.create_preflight(
            preflight_id=preflight_id,
            preview_run_id=request.preview_run_id,
            status=DeletePreflightStatus.ready.value,
            selected_item_ids=selected_ids,
            selected_key_count=evidence.selected_key_count,
            selection_hash=evidence.selection_hash,
            keyset_hash=evidence.keyset_hash,
            db_fingerprint_hash=guard.fingerprint_hash,
            db_target_class=guard.target_class,
            rollback_ready=True,
            rollback_blockers=[],
            expires_at=expires_at.isoformat(),
            timestamp_start_date=format_date(evidence.timestamp_start_date),
            timestamp_end_date=format_date(evidence.timestamp_end_date),
        )
        self._audit(
            action="upload.delete_preflight",
            target_type="delete_preflight",
            target_id=preflight_id,
            result=AuditResult.success,
            params=self._audit_params(
                preview_run_id=request.preview_run_id,
                preflight_id=preflight_id,
                selected_item_count=evidence.selected_item_count,
                selected_key_count=evidence.selected_key_count,
                rollback_ready=True,
                rollback_blockers=[],
                guard=guard,
                selection_hash=evidence.selection_hash,
                keyset_hash=evidence.keyset_hash,
                timestamp_start_date=evidence.timestamp_start_date,
                timestamp_end_date=evidence.timestamp_end_date,
            ),
        )
        return DeletePreflightResponse(
            preflight_id=preflight_id,
            status=DeletePreflightStatus.ready,
            selected_item_count=evidence.selected_item_count,
            selected_key_count=evidence.selected_key_count,
            rollback_ready=True,
            rollback_blockers=[],
            db_target_guard=guard.to_api(),
            selection_hash=evidence.selection_hash,
            keyset_hash=evidence.keyset_hash,
            expires_at=expires_at,
            timestamp_start_date=evidence.timestamp_start_date,
            timestamp_end_date=evidence.timestamp_end_date,
        )

    def start_delete(self, request: DeleteJobCreateRequest) -> DeleteJobCreateResponse:
        preflight = self.repository.get_preflight(request.preflight_id)
        if preflight is None:
            self._reject_with_blocked_audit("preflight_missing", None, request.preflight_id)
        if str(preflight["status"]) != DeletePreflightStatus.ready.value:
            self._reject_with_blocked_audit("preflight_not_ready", None, request.preflight_id)
        expires_at = parse_dt(str(preflight["expires_at"]))
        if expires_at is None or expires_at < utc_now():
            self.repository.expire_preflight(str(preflight["preflight_id"]))
            self._reject_with_blocked_audit("preflight_expired", str(preflight["preview_run_id"]), request.preflight_id)
        typed_count = request.typed_delete_keys.replace(",", "").strip()
        if not typed_count.isdigit() or int(typed_count) != request.expected_delete_keys:
            self._reject_with_blocked_audit("typed_delete_keys_mismatch", str(preflight["preview_run_id"]), request.preflight_id)
        if not request.acknowledge_no_undo or not request.acknowledge_rollback_requires_fresh_preview_and_start_upload:
            self._reject_with_blocked_audit("delete_acknowledgement_required", str(preflight["preview_run_id"]), request.preflight_id)
        if int(preflight["selected_key_count"]) != request.expected_delete_keys:
            self._reject_with_blocked_audit("expected_delete_keys_mismatch", str(preflight["preview_run_id"]), request.preflight_id)
        selected_ids = self.repository.selected_item_ids_for_preflight(preflight)
        blocker = self._common_start_blocker()
        if blocker:
            self._reject_with_blocked_audit(blocker, str(preflight["preview_run_id"]), request.preflight_id)
        runtime_ok, runtime_reason = self.runtime_ready()
        if not runtime_ok:
            self._reject_with_blocked_audit(runtime_reason or "runtime_not_ready", str(preflight["preview_run_id"]), request.preflight_id)
        preview = self.repository.get_preview_run(str(preflight["preview_run_id"]))
        preview_blocker = self._preview_blocker(preview, str(preflight["preview_run_id"]))
        if preview_blocker:
            self._reject_with_blocked_audit(preview_blocker, str(preflight["preview_run_id"]), request.preflight_id)
        items = self.repository.get_preview_items(str(preflight["preview_run_id"]), selected_ids)
        if len(items) != len(selected_ids):
            self._reject_with_blocked_audit("selection_item_missing", str(preflight["preview_run_id"]), request.preflight_id)
        if any(str(item["status"]) != "already_in_db" for item in items):
            self._reject_with_blocked_audit("selection_status_changed", str(preflight["preview_run_id"]), request.preflight_id)
        timestamp_scope = timestamp_scope_from_preflight(preflight)
        evidence = self._build_key_evidence(items, timestamp_scope=timestamp_scope)
        if not evidence.rollback_ready:
            self._reject_with_blocked_audit(self._key_evidence_failure_reason(evidence), str(preflight["preview_run_id"]), request.preflight_id)
        if evidence.selection_hash != str(preflight["selection_hash"]) or evidence.keyset_hash != str(preflight["keyset_hash"]):
            self._reject_with_blocked_audit("keyset_mismatch", str(preflight["preview_run_id"]), request.preflight_id)
        guard = self.db_client.guard()
        if not guard.passed:
            self._reject_with_blocked_audit(guard.reason_code or "db_target_guard_failed", str(preflight["preview_run_id"]), request.preflight_id)
        if guard.fingerprint_hash != str(preflight["db_fingerprint_hash"]):
            self._reject_with_blocked_audit("db_target_changed", str(preflight["preview_run_id"]), request.preflight_id)
        try:
            db_count = self.db_client.count_existing_keys(evidence.keys)
        except DeleteDbBlockedError as error:
            self._reject_with_blocked_audit(error.reason, str(preflight["preview_run_id"]), request.preflight_id)
        except Exception:
            self._reject_with_blocked_audit("db_count_check_failed", str(preflight["preview_run_id"]), request.preflight_id)
        if db_count != evidence.selected_key_count:
            self._reject_with_blocked_audit("db_key_count_mismatch", str(preflight["preview_run_id"]), request.preflight_id)
        delete_run_id = f"del_{uuid4().hex[:12]}"
        try:
            result = self.repository.create_delete_run_preparing(
                delete_run_id=delete_run_id,
                preflight_id=str(preflight["preflight_id"]),
                preview_run_id=str(preflight["preview_run_id"]),
                expected_key_count=evidence.selected_key_count,
                db_fingerprint_hash=guard.fingerprint_hash or "",
                selection_hash=evidence.selection_hash,
                keyset_hash=evidence.keyset_hash,
                rollback_ready=evidence.rollback_ready,
                selected_items=evidence.items,
            )
        except Exception as error:
            raise DeleteRejectedError("delete_run_state_write_failed", status_code=500) from error
        if result.active_delete_run_id:
            self._reject_with_blocked_audit("active_delete_job_exists", str(preflight["preview_run_id"]), request.preflight_id)
        try:
            start_audit_id = self._audit(
                action="upload.delete_start",
                target_type="delete_run",
                target_id=delete_run_id,
                result=AuditResult.success,
                params=self._audit_params(
                    preview_run_id=str(preflight["preview_run_id"]),
                    preflight_id=str(preflight["preflight_id"]),
                    delete_run_id=delete_run_id,
                    selected_item_count=evidence.selected_item_count,
                    selected_key_count=evidence.selected_key_count,
                    rollback_ready=evidence.rollback_ready,
                    rollback_blockers=[],
                    guard=guard,
                    selection_hash=evidence.selection_hash,
                    keyset_hash=evidence.keyset_hash,
                    timestamp_start_date=evidence.timestamp_start_date,
                    timestamp_end_date=evidence.timestamp_end_date,
                ),
            )
        except Exception as error:
            self.repository.mark_status(
                delete_run_id,
                DeleteRunStatus.blocked.value,
                error_code="audit_write_failed",
                error_message="Start audit write failed before DB mutation.",
                finish=True,
            )
            self.repository.mark_items(delete_run_id, "blocked", "audit_write_failed")
            raise DeleteRejectedError("audit_write_failed", status_code=500) from error
        if not self.repository.set_start_audit_id(delete_run_id, start_audit_id):
            self._block_created_run(delete_run_id, "delete_run_state_write_failed")
        if not self.repository.mark_running(delete_run_id):
            self._block_created_run(delete_run_id, "delete_run_state_write_failed")
        try:
            deleted = self.db_client.delete_keys(evidence.keys, expected_count=evidence.selected_key_count)
        except DeleteDbBlockedError as error:
            self.repository.mark_status(
                delete_run_id,
                DeleteRunStatus.blocked.value,
                error_code=error.reason,
                error_message=error.reason,
                finish=True,
            )
            self.repository.mark_items(delete_run_id, "blocked", error.reason)
            self._audit_delete_outcome(delete_run_id, preflight, evidence, guard, "upload.delete_blocked", AuditResult.blocked, error.reason)
            raise DeleteRejectedError(error.reason, status_code=422) from error
        except DeleteCommitUnknownError as error:
            self.repository.mark_status(
                delete_run_id,
                DeleteRunStatus.commit_unknown.value,
                recovery_required=True,
                error_code="commit_unknown",
                error_message="Delete outcome must be reconciled before retry.",
            )
            self.repository.mark_items(delete_run_id, "unknown", "commit_unknown")
            self._audit_delete_outcome(
                delete_run_id,
                preflight,
                evidence,
                guard,
                "upload.delete_failed",
                AuditResult.failure,
                "commit_unknown",
            )
            raise DeleteRejectedError("commit_unknown", status_code=500) from error
        except Exception as error:
            reason = error.reason if isinstance(error, DeleteDbFailedError) else "delete_transaction_failed"
            self.repository.mark_status(
                delete_run_id,
                DeleteRunStatus.failed.value,
                error_code=reason,
                error_message=reason,
                finish=True,
            )
            self.repository.mark_items(delete_run_id, "failed", reason)
            self._audit_delete_outcome(delete_run_id, preflight, evidence, guard, "upload.delete_failed", AuditResult.failure, reason)
            raise DeleteRejectedError(reason, status_code=500) from error
        self.repository.mark_status(delete_run_id, DeleteRunStatus.finalizing.value, deleted_key_count=deleted)
        self.repository.mark_items(delete_run_id, "deleted")
        self.repository.mark_status(
            delete_run_id,
            DeleteRunStatus.succeeded.value,
            deleted_key_count=deleted,
            recovery_required=False,
            finish=True,
        )
        self._audit_delete_outcome(delete_run_id, preflight, evidence, guard, "upload.delete_succeeded", AuditResult.success, None, deleted)
        return DeleteJobCreateResponse(
            delete_run_id=delete_run_id,
            status=DeleteRunStatus.succeeded,
            expected_delete_keys=evidence.selected_key_count,
            deleted_keys=deleted,
            rollback_ready=evidence.rollback_ready,
            recovery_required=False,
        )

    def reconcile(self, delete_run_id: str, *, acknowledge_retry: bool = False) -> DeleteReconcileResponse:
        row = self.repository.get_run(delete_run_id)
        if row is None:
            raise DeleteRejectedError("delete_run_missing", status_code=404)
        status = str(row["status"])
        if status == DeleteRunStatus.reconciliation_failed.value and not acknowledge_retry:
            raise DeleteRejectedError("reconciliation_retry_acknowledgement_required", status_code=422)
        if status not in {DeleteRunStatus.commit_unknown.value, DeleteRunStatus.reconciliation_failed.value}:
            raise DeleteRejectedError("delete_run_not_reconcilable", status_code=409)
        preflight = self.repository.get_preflight(str(row["preflight_id"]))
        if preflight is None:
            raise DeleteRejectedError("preflight_missing", status_code=404)
        selected_ids = self.repository.selected_item_ids_for_preflight(preflight)
        items = self.repository.get_preview_items(str(preflight["preview_run_id"]), selected_ids)
        expected_key_count = int(row["expected_key_count"] or 0)
        if len(items) != len(selected_ids):
            return self._finish_reconcile(delete_run_id, row, expected_key_count, 0, 0, "reconciliation_failed", "selection_item_missing")
        if any(str(item["status"]) != "already_in_db" for item in items):
            return self._finish_reconcile(delete_run_id, row, expected_key_count, 0, 0, "reconciliation_failed", "selection_status_changed")
        timestamp_scope = timestamp_scope_from_preflight(preflight)
        evidence = self._build_key_evidence(items, timestamp_scope=timestamp_scope)
        if not evidence.rollback_ready:
            return self._finish_reconcile(
                delete_run_id,
                row,
                expected_key_count,
                0,
                0,
                "reconciliation_failed",
                self._key_evidence_failure_reason(evidence),
            )
        if evidence.selection_hash != str(row["selection_hash"]) or evidence.keyset_hash != str(row["keyset_hash"]):
            return self._finish_reconcile(delete_run_id, row, expected_key_count, 0, 0, "reconciliation_failed", "keyset_mismatch")
        guard = self.db_client.target_guard()
        if not guard.passed or guard.fingerprint_hash != str(row["db_fingerprint_hash"]):
            return self._finish_reconcile(delete_run_id, row, expected_key_count, 0, 0, "reconciliation_failed", "db_target_changed")
        self.repository.mark_status(delete_run_id, DeleteRunStatus.reconciling.value, recovery_required=True)
        try:
            present = self.db_client.count_existing_keys(evidence.keys)
        except DeleteDbBlockedError as error:
            return self._finish_reconcile(delete_run_id, row, expected_key_count, 0, 0, "reconciliation_failed", error.reason)
        except Exception:
            return self._finish_reconcile(delete_run_id, row, expected_key_count, 0, 0, "reconciliation_failed", "reconciliation_count_failed")
        absent = max(0, expected_key_count - present)
        if present == 0:
            status_value = DeleteRunStatus.reconciled_succeeded.value
            reason = None
        elif present == expected_key_count:
            status_value = DeleteRunStatus.reconciled_rolled_back.value
            reason = None
        else:
            status_value = DeleteRunStatus.reconciliation_failed.value
            reason = "mixed_key_presence"
        return self._finish_reconcile(delete_run_id, row, expected_key_count, present, absent, status_value, reason)

    def _finish_reconcile(
        self,
        delete_run_id: str,
        row: sqlite3.Row,
        expected: int,
        present: int,
        absent: int,
        status_value: str,
        reason: str | None,
    ) -> DeleteReconcileResponse:
        success = status_value in {
            DeleteRunStatus.reconciled_succeeded.value,
            DeleteRunStatus.reconciled_rolled_back.value,
        }
        self.repository.mark_status(
            delete_run_id,
            status_value,
            recovery_required=not success,
            error_code=reason,
            error_message=reason,
            clear_error=success,
            finish=success,
        )
        self._audit(
            action="upload.delete_reconciled",
            target_type="delete_run",
            target_id=delete_run_id,
            result=AuditResult.success if success else AuditResult.failure,
            params={
                "deleteRunId": delete_run_id,
                "preflightId": str(row["preflight_id"]),
                "previewRunId": str(row["preview_run_id"]),
                "selectedRowCount": expected,
                "rowsPresent": present,
                "rowsAbsent": absent,
                "recoveryRequired": not success,
                "reasonCode": reason,
                "rawMatchRowsReturned": False,
            },
            error_code=reason,
        )
        return DeleteReconcileResponse(
            delete_run_id=delete_run_id,
            status=DeleteRunStatus(status_value),
            expected_delete_keys=expected,
            keys_present=present,
            keys_absent=absent,
            recovery_required=not success,
        )

    def _blocked_preflight(
        self,
        preflight_id: str,
        request: DeletePreflightRequest,
        reason: str,
        *,
        evidence: KeyEvidence | None = None,
        guard: DbGuardResult | None = None,
        rollback_blockers: list[str] | None = None,
    ) -> DeletePreflightResponse:
        selected_ids = sorted(set(request.preview_item_ids))
        selected_key_count = evidence.selected_key_count if evidence else 0
        selection_hash = evidence.selection_hash if evidence else safe_hash({"previewRunId": request.preview_run_id, "selectedItemIds": selected_ids})
        keyset_hash = evidence.keyset_hash if evidence else safe_hash({"keys": []})
        timestamp_start_date = evidence.timestamp_start_date if evidence else request.timestamp_start_date
        timestamp_end_date = evidence.timestamp_end_date if evidence else request.timestamp_end_date
        blockers = rollback_blockers if rollback_blockers is not None else []
        guard = guard or DbGuardResult(False, "unknown", None, reason)
        expires_at = utc_now() + timedelta(seconds=PREFLIGHT_TTL_SECONDS)
        self.repository.create_preflight(
            preflight_id=preflight_id,
            preview_run_id=request.preview_run_id,
            status=DeletePreflightStatus.blocked.value,
            selected_item_ids=selected_ids,
            selected_key_count=selected_key_count,
            selection_hash=selection_hash,
            keyset_hash=keyset_hash,
            db_fingerprint_hash=guard.fingerprint_hash,
            db_target_class=guard.target_class,
            rollback_ready=False,
            rollback_blockers=blockers,
            expires_at=expires_at.isoformat(),
            timestamp_start_date=format_date(timestamp_start_date),
            timestamp_end_date=format_date(timestamp_end_date),
            reason_code=reason,
            error_message=reason,
        )
        self._audit(
            action="upload.delete_preflight",
            target_type="delete_preflight",
            target_id=preflight_id,
            result=AuditResult.blocked,
            params=self._audit_params(
                preview_run_id=request.preview_run_id,
                preflight_id=preflight_id,
                selected_item_count=len(selected_ids),
                selected_key_count=selected_key_count,
                rollback_ready=False,
                rollback_blockers=blockers,
                guard=guard,
                selection_hash=selection_hash,
                keyset_hash=keyset_hash,
                timestamp_start_date=timestamp_start_date,
                timestamp_end_date=timestamp_end_date,
                reason_code=reason,
            ),
            error_code=reason,
            error_message=reason,
        )
        return DeletePreflightResponse(
            preflight_id=preflight_id,
            status=DeletePreflightStatus.blocked,
            selected_item_count=len(selected_ids),
            selected_key_count=selected_key_count,
            rollback_ready=False,
            rollback_blockers=blockers,
            db_target_guard=guard.to_api(),
            selection_hash=selection_hash,
            keyset_hash=keyset_hash,
            expires_at=expires_at,
            reason_code=reason,
            timestamp_start_date=timestamp_start_date,
            timestamp_end_date=timestamp_end_date,
        )

    def _reject_with_blocked_audit(self, reason: str, preview_run_id: str | None, preflight_id: str | None) -> None:
        self._audit(
            action="upload.delete_blocked",
            target_type="delete_preflight",
            target_id=preflight_id,
            result=AuditResult.blocked,
            params={
                "previewRunId": preview_run_id,
                "preflightId": preflight_id,
                "reasonCode": reason,
                "rawMatchRowsReturned": False,
            },
            error_code=reason,
            error_message=reason,
        )
        raise DeleteRejectedError(reason, status_code=409 if reason.endswith("_exists") else 422)

    def _block_created_run(self, delete_run_id: str, reason: str) -> None:
        self.repository.mark_status(delete_run_id, DeleteRunStatus.blocked.value, error_code=reason, error_message=reason, finish=True)
        self.repository.mark_items(delete_run_id, "blocked", reason)
        self._audit(
            action="upload.delete_blocked",
            target_type="delete_run",
            target_id=delete_run_id,
            result=AuditResult.blocked,
            params={"deleteRunId": delete_run_id, "reasonCode": reason, "rawMatchRowsReturned": False},
            error_code=reason,
            error_message=reason,
        )
        raise DeleteRejectedError(reason, status_code=500)

    def _audit_delete_outcome(
        self,
        delete_run_id: str,
        preflight: sqlite3.Row,
        evidence: KeyEvidence,
        guard: DbGuardResult,
        action: str,
        result: AuditResult,
        reason: str | None,
        deleted_count: int = 0,
    ) -> None:
        self._audit(
            action=action,
            target_type="delete_run",
            target_id=delete_run_id,
            result=result,
            params=self._audit_params(
                preview_run_id=str(preflight["preview_run_id"]),
                preflight_id=str(preflight["preflight_id"]),
                delete_run_id=delete_run_id,
                selected_item_count=evidence.selected_item_count,
                selected_key_count=evidence.selected_key_count,
                deleted_key_count=deleted_count,
                rollback_ready=evidence.rollback_ready,
                rollback_blockers=[],
                guard=guard,
                selection_hash=evidence.selection_hash,
                keyset_hash=evidence.keyset_hash,
                timestamp_start_date=evidence.timestamp_start_date,
                timestamp_end_date=evidence.timestamp_end_date,
                reason_code=reason,
            ),
            error_code=reason,
            error_message=reason,
        )

    def _common_start_blocker(self) -> str | None:
        if self.repository.has_active_preview_run() is not None:
            return "active_preview_exists"
        if self.repository.has_active_upload_job() is not None:
            return "active_upload_job_exists"
        if self.repository.get_active_delete_run_id() is not None:
            return "active_delete_job_exists"
        return None

    def _preview_blocker(self, preview: sqlite3.Row | None, preview_run_id: str) -> str | None:
        if preview is None:
            return "preview_missing"
        latest = self.repository.get_latest_preview_run_id()
        if latest is not None and latest != preview_run_id:
            return "preview_not_latest"
        reference = preview_reference_time(preview)
        if reference is None:
            return "preview_freshness_unknown"
        if (utc_now() - reference).total_seconds() > PREVIEW_FRESHNESS_MAX_AGE_SECONDS:
            return "preview_stale"
        if str(preview["status"]) != "succeeded":
            return "preview_not_succeeded"
        if str(preview["db_status"]) != "reachable":
            return "preview_db_not_reachable"
        return None

    def _build_key_evidence(
        self,
        items: list[sqlite3.Row],
        *,
        timestamp_scope: tuple[date | None, date | None] = (None, None),
    ) -> KeyEvidence:
        keys: set[tuple[str, str]] = set()
        blockers: list[str] = []
        timestamp_start_date, timestamp_end_date = timestamp_scope
        for item in items:
            extraction, blocker = self._extract_item_keys(item)
            if blocker is not None:
                blockers.append(blocker)
                continue
            if extraction is None:
                blockers.append("file_missing")
                continue
            expected_local_count = int(item["local_key_count"] or 0)
            if expected_local_count <= 0 or len(extraction.local_keys) != expected_local_count:
                blockers.append("keyset_mismatch")
                continue
            item_keys = extraction.local_keys
            if timestamp_start_date is not None and timestamp_end_date is not None:
                item_keys = filter_keys_by_timestamp_date(item_keys, timestamp_start_date, timestamp_end_date)
            keys.update(item_keys)
        selected_ids = [int(item["preview_item_id"]) for item in items]
        keyset_hash = hash_keys(keys)
        selection_hash = safe_hash(
            {
                "previewItemIds": selected_ids,
                "itemEvidence": [
                    {
                        "previewItemId": int(item["preview_item_id"]),
                        "fileSignature": str(item["file_signature"]),
                        "localKeyCount": int(item["local_key_count"] or 0),
                        "dbMatchCount": int(item["db_match_count"] or 0),
                    }
                    for item in items
                ],
                "keysetHash": keyset_hash,
                "timestampDateScope": {
                    "startDate": format_date(timestamp_start_date),
                    "endDate": format_date(timestamp_end_date),
                },
            }
        )
        unique_blockers = sorted(set(blockers))
        return KeyEvidence(
            keys=keys,
            selected_item_ids=selected_ids,
            selected_item_count=len(items),
            selected_key_count=len(keys),
            selection_hash=selection_hash,
            keyset_hash=keyset_hash,
            rollback_ready=not unique_blockers,
            rollback_blockers=unique_blockers,
            items=items,
            timestamp_start_date=timestamp_start_date,
            timestamp_end_date=timestamp_end_date,
        )

    def _extract_item_keys(self, item: sqlite3.Row) -> tuple[KeyExtractionResult | None, str | None]:
        path = Path(str(item["path"]))
        try:
            stat = path.stat()
        except OSError:
            return None, "file_missing"
        if build_file_signature(path, stat) != str(item["file_signature"]):
            return None, "file_signature_changed"
        file_date = None
        if item["file_date"]:
            try:
                file_date = datetime.fromisoformat(str(item["file_date"])).date()
            except ValueError:
                file_date = None
        candidate = CandidateFile(
            source=SourceFolder(str(item["folder_label"]), str(item["kind"]), Path(str(item["folder_path"]))),
            path=path,
            file_date=file_date,
            stat=stat,
        )
        try:
            return (
                self.extractor.extract(
                    candidate,
                    max_file_seconds=300,
                    sample_rows=200,
                    force_full_scan=True,
                ),
                None,
            )
        except Exception:
            return None, "keyset_mismatch"

    def _key_evidence_failure_reason(self, evidence: KeyEvidence) -> str:
        if len(evidence.rollback_blockers) == 1:
            return evidence.rollback_blockers[0]
        return "keyset_mismatch"

    def _audit(self, **kwargs) -> int:
        return self.audit_repository.insert_audit(**kwargs)

    def _audit_params(
        self,
        *,
        preview_run_id: str | None,
        preflight_id: str | None = None,
        delete_run_id: str | None = None,
        selected_item_count: int = 0,
        selected_key_count: int = 0,
        deleted_key_count: int = 0,
        rollback_ready: bool = False,
        rollback_blockers: list[str] | None = None,
        guard: DbGuardResult | None = None,
        selection_hash: str | None = None,
        keyset_hash: str | None = None,
        timestamp_start_date: date | None = None,
        timestamp_end_date: date | None = None,
        reason_code: str | None = None,
    ) -> dict[str, object]:
        return {
            "previewRunId": preview_run_id,
            "preflightId": preflight_id,
            "deleteRunId": delete_run_id,
            "selectedItemCount": selected_item_count,
            "selectedRowCount": selected_key_count,
            "deletedRowCount": deleted_key_count,
            "rollbackReady": rollback_ready,
            "rollbackBlockers": rollback_blockers or [],
            "dbTargetClass": guard.target_class if guard else None,
            "dbFingerprintHash": guard.fingerprint_hash if guard else None,
            "selectionHash": selection_hash,
            "selectionDataHash": keyset_hash,
            "timestampStartDate": format_date(timestamp_start_date),
            "timestampEndDate": format_date(timestamp_end_date),
            "reasonCode": reason_code,
            "rawMatchRowsReturned": False,
        }


def safe_hash(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def hash_keys(keys: set[tuple[str, str]]) -> str:
    return safe_hash({"keys": sorted([{"timestamp": ts, "deviceId": device_id} for ts, device_id in keys], key=lambda item: (item["timestamp"], item["deviceId"]))})


def format_date(value: date | None) -> str | None:
    return None if value is None else value.isoformat()


def timestamp_scope_from_request(request: DeletePreflightRequest) -> tuple[date | None, date | None]:
    return request.timestamp_start_date, request.timestamp_end_date


def timestamp_scope_from_preflight(preflight: sqlite3.Row) -> tuple[date | None, date | None]:
    return parse_date_value(preflight["timestamp_start_date"]), parse_date_value(preflight["timestamp_end_date"])


def parse_date_value(value: object) -> date | None:
    if value is None:
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def filter_keys_by_timestamp_date(
    keys: set[tuple[str, str]],
    start_date: date,
    end_date: date,
) -> set[tuple[str, str]]:
    return {
        (timestamp, device_id)
        for timestamp, device_id in keys
        if timestamp_date_in_scope(timestamp, start_date, end_date)
    }


def timestamp_date_in_scope(timestamp: str, start_date: date, end_date: date) -> bool:
    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return False
    timestamp_date = parsed.date()
    return start_date <= timestamp_date <= end_date


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def preview_reference_time(preview: sqlite3.Row) -> datetime | None:
    return (
        parse_dt(preview["finished_at"])
        or parse_dt(preview["started_at"])
        or parse_dt(preview["requested_at"])
    )


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def classify_database_name(value: str) -> str:
    return "default_postgres" if value == "postgres" else "configured_database"


def classify_project_id(value: str) -> str:
    return "expected_project_id" if value else "missing_project_id"


def default_runtime_ready(settings: Settings) -> tuple[bool, str | None]:
    try:
        from backend.app.services.command_runner import AllowedCommandRunner
        from backend.app.services.runtime_control import runtime_core_ready
        from backend.app.services.runtime_readiness import RuntimeReadinessService

        runner = AllowedCommandRunner(
            settings.local_supabase_project_path,
            settings.runtime_command_timeout_seconds,
            project_id=settings.local_supabase_project_id,
        )
        status = RuntimeReadinessService(settings, runner).check_status()
        if runtime_core_ready(status):
            return True, None
        return False, status.reason_code or "runtime_not_ready"
    except Exception:
        return False, "runtime_status_unavailable"
