from __future__ import annotations

import os
import re
import sqlite3
import stat
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterator

AUTHORITY_SCHEMA_VERSION = 1
AUTHORITY_JOURNAL_MODE = "delete"
MAX_COORDINATOR_GENERATION = (1 << 63) - 1
COORDINATOR_STATE_VALUES = (
    "idle",
    "claimed",
    "active",
    "commit_unknown_blocked",
    "cleanup_blocked",
)
COORDINATOR_CONSUMER_VALUES = (
    "settings_save",
    "local_supabase_start",
    "local_supabase_stop",
    "manifest_preparation",
    "target_identity_preparation",
    "preview",
    "start",
    "retry",
    "delete_preflight",
    "delete",
    "reconcile",
    "delete_disposition",
    "delete_restore",
    "recovery",
    "final_signoff",
)
COORDINATOR_STATES = frozenset(COORDINATOR_STATE_VALUES)
COORDINATOR_CONSUMERS = frozenset(COORDINATOR_CONSUMER_VALUES)
_COORDINATOR_STATES_SQL = ",".join(f"'{value}'" for value in COORDINATOR_STATE_VALUES)
_COORDINATOR_CONSUMERS_SQL = ",".join(f"'{value}'" for value in COORDINATOR_CONSUMER_VALUES)
_IDENTIFIER_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,255}\Z")


class OperationAuthorityError(RuntimeError):
    """Base error for the protected machine authority store."""


class OperationAuthorityUnavailableError(OperationAuthorityError):
    """Raised when the pre-provisioned authority store cannot be opened safely."""


class OperationAuthorityBindingError(OperationAuthorityError):
    """Raised when the opened store is not the pre-bound authority/coordinator."""


@dataclass(frozen=True)
class AuthoritySecurityAttestation:
    security_evidence_id: str
    file_binding_id: str
    generation_evidence_id: str
    generation_floor: int


AuthoritySecurityVerifier = Callable[[Path], AuthoritySecurityAttestation]
AuthorityProvisioningParentVerifier = Callable[[Path], str]
AuthorityGenerationFloorAdvancer = Callable[[Path, int, int], None]
_AUTHORITY_SIDECAR_SUFFIXES = ("-journal", "-wal", "-shm")


@dataclass(frozen=True)
class CoordinatorSnapshot:
    coordinator_id: str
    state: str
    owner_id: str | None
    consumer: str | None
    generation: int
    claim_base_generation: int | None
    active_base_generation: int | None
    block_base_generation: int | None
    claim_evidence_id: str | None
    active_evidence_id: str | None
    block_evidence_id: str | None
    updated_at: str


@dataclass(frozen=True)
class CoordinatorTransitionResult:
    applied: bool
    idempotent: bool
    reason: str | None
    snapshot: CoordinatorSnapshot


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _required_identifier(value: str, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field}_invalid")
    normalized = value.strip()
    if _IDENTIFIER_PATTERN.fullmatch(normalized) is None:
        raise ValueError(f"{field}_invalid")
    return normalized


def _stored_identifier(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise OperationAuthorityBindingError(f"{field}_invalid")
    try:
        return _required_identifier(value, field)
    except ValueError as exc:
        raise OperationAuthorityBindingError(f"{field}_invalid") from exc


def _strict_generation(value: object, field: str) -> int:
    if type(value) is not int or not 0 <= value <= MAX_COORDINATOR_GENERATION:
        raise OperationAuthorityBindingError(f"{field}_invalid")
    return value


def _required_transition_generation(value: object) -> int:
    if type(value) is not int or not 0 <= value < MAX_COORDINATOR_GENERATION:
        raise ValueError("expected_generation_invalid")
    return value


def _reject_link_or_reparse_components(path: Path) -> None:
    for component in (path, *path.parents):
        try:
            if component.is_symlink():
                raise OperationAuthorityUnavailableError("machine_authority_path_has_link_component")
            attributes = getattr(component.stat(follow_symlinks=False), "st_file_attributes", 0)
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise OperationAuthorityUnavailableError("machine_authority_path_unreadable") from exc
        if attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0):
            raise OperationAuthorityUnavailableError("machine_authority_path_has_reparse_component")


def _absolute_regular_path(value: str | Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise OperationAuthorityUnavailableError("machine_authority_path_not_absolute")
    _reject_link_or_reparse_components(path)
    try:
        path.stat(follow_symlinks=False)
    except FileNotFoundError as exc:
        raise OperationAuthorityUnavailableError("machine_authority_not_provisioned") from exc
    except OSError as exc:
        raise OperationAuthorityUnavailableError("machine_authority_path_unreadable") from exc
    if not path.is_file():
        raise OperationAuthorityUnavailableError("machine_authority_not_regular_file")
    return path.resolve(strict=True)


def _reject_linked_authority_sidecars(path: Path) -> None:
    for suffix in _AUTHORITY_SIDECAR_SUFFIXES:
        sidecar = Path(f"{path}{suffix}")
        _reject_link_or_reparse_components(sidecar)


def _reject_preexisting_authority_sidecars(path: Path) -> None:
    """Refuse provisioning when any SQLite sidecar name is already occupied."""

    for suffix in _AUTHORITY_SIDECAR_SUFFIXES:
        sidecar = Path(f"{path}{suffix}")
        _reject_link_or_reparse_components(sidecar)
        if os.path.lexists(sidecar):
            raise OperationAuthorityUnavailableError(
                "machine_authority_sidecar_already_exists"
            )


def _cleanup_failed_provision(path: Path, created_identity: tuple[int, int]) -> None:
    """Remove only the database file still owned by this provisioning attempt.

    SQLite sidecars are intentionally left untouched because their ownership
    cannot be proven after a failed open or transaction. A later provision
    remains fail-closed until an installer-controlled cleanup handles them.
    """

    try:
        current = path.stat(follow_symlinks=False)
    except FileNotFoundError:
        return
    except OSError as exc:
        raise OperationAuthorityUnavailableError(
            "machine_authority_provisioning_cleanup_failed"
        ) from exc
    if (int(current.st_dev), int(current.st_ino)) != created_identity:
        raise OperationAuthorityUnavailableError(
            "machine_authority_provisioning_cleanup_identity_mismatch"
        )

    try:
        path.unlink()
    except (OSError, OperationAuthorityError) as exc:
        raise OperationAuthorityUnavailableError(
            "machine_authority_provisioning_cleanup_failed"
        ) from exc


def _observe_security_boundary(
    verifier: AuthoritySecurityVerifier,
    path: Path,
) -> AuthoritySecurityAttestation:
    try:
        attestation = verifier(path)
        if not isinstance(attestation, AuthoritySecurityAttestation):
            raise ValueError("security_attestation_invalid")
        return AuthoritySecurityAttestation(
            security_evidence_id=_required_identifier(
                attestation.security_evidence_id,
                "observed_security_evidence_id",
            ),
            file_binding_id=_required_identifier(
                attestation.file_binding_id,
                "observed_file_binding_id",
            ),
            generation_evidence_id=_required_identifier(
                attestation.generation_evidence_id,
                "observed_generation_evidence_id",
            ),
            generation_floor=_strict_generation(
                attestation.generation_floor,
                "observed_generation_floor",
            ),
        )
    except OperationAuthorityError:
        raise
    except Exception as exc:
        raise OperationAuthorityUnavailableError("machine_authority_security_verification_failed") from exc


def _observe_provisioning_parent(
    verifier: AuthorityProvisioningParentVerifier,
    path: Path,
) -> str:
    try:
        return _required_identifier(verifier(path), "observed_parent_security_evidence_id")
    except OperationAuthorityError:
        raise
    except Exception as exc:
        raise OperationAuthorityUnavailableError("machine_authority_parent_verification_failed") from exc


class OperationAuthorityRepository:
    """CAS repository for the fixed machine-global operation coordinator.

    Construction never creates the database. Provisioning is an explicit,
    separate administrative action. Callers must provide the pre-bound authority,
    coordinator, and security-evidence ids plus a verifier for the protected
    directory, database, and SQLite sidecar boundary so first observation cannot
    accept a substituted store.
    """

    def __init__(
        self,
        db_path: str | Path,
        *,
        expected_authority_id: str,
        expected_coordinator_id: str,
        expected_security_evidence_id: str,
        expected_file_binding_id: str,
        expected_generation_evidence_id: str,
        verify_security_boundary: AuthoritySecurityVerifier,
        advance_generation_floor: AuthorityGenerationFloorAdvancer,
    ) -> None:
        self.db_path = _absolute_regular_path(db_path)
        self.expected_authority_id = _required_identifier(expected_authority_id, "expected_authority_id")
        self.expected_coordinator_id = _required_identifier(expected_coordinator_id, "expected_coordinator_id")
        self.expected_security_evidence_id = _required_identifier(
            expected_security_evidence_id,
            "expected_security_evidence_id",
        )
        self.expected_file_binding_id = _required_identifier(
            expected_file_binding_id,
            "expected_file_binding_id",
        )
        self.expected_generation_evidence_id = _required_identifier(
            expected_generation_evidence_id,
            "expected_generation_evidence_id",
        )
        self.verify_security_boundary = verify_security_boundary
        self.advance_generation_floor = advance_generation_floor
        self._verify_security_boundary()
        self._file_identity = self._read_file_identity()
        with self._connect() as connection:
            self._validate_binding(connection)

    @classmethod
    def provision(
        cls,
        db_path: str | Path,
        *,
        authority_id: str,
        coordinator_id: str,
        initial_evidence_id: str,
        expected_parent_security_evidence_id: str,
        expected_security_evidence_id: str,
        expected_generation_evidence_id: str,
        verify_provisioning_parent: AuthorityProvisioningParentVerifier,
        verify_security_boundary: AuthoritySecurityVerifier,
        advance_generation_floor: AuthorityGenerationFloorAdvancer,
    ) -> OperationAuthorityRepository:
        """Explicitly create one empty authority store without overwriting a file.

        This method is intentionally not called by application startup. Machine
        installation/ACL provisioning remains a separate controlled operation.
        """

        path = Path(db_path).expanduser()
        if not path.is_absolute():
            raise OperationAuthorityUnavailableError("machine_authority_path_not_absolute")
        if not path.parent.is_dir():
            raise OperationAuthorityUnavailableError("machine_authority_parent_missing")
        _reject_link_or_reparse_components(path.parent)

        authority = _required_identifier(authority_id, "authority_id")
        coordinator = _required_identifier(coordinator_id, "coordinator_id")
        evidence = _required_identifier(initial_evidence_id, "initial_evidence_id")
        expected_security = _required_identifier(
            expected_security_evidence_id,
            "expected_security_evidence_id",
        )
        expected_parent_security = _required_identifier(
            expected_parent_security_evidence_id,
            "expected_parent_security_evidence_id",
        )
        expected_generation_evidence = _required_identifier(
            expected_generation_evidence_id,
            "expected_generation_evidence_id",
        )
        observed_parent_security = _observe_provisioning_parent(verify_provisioning_parent, path)
        if observed_parent_security != expected_parent_security:
            raise OperationAuthorityBindingError("machine_authority_parent_security_evidence_mismatch")
        _reject_preexisting_authority_sidecars(path)
        try:
            descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o600)
        except FileExistsError as exc:
            raise OperationAuthorityUnavailableError("machine_authority_already_exists") from exc
        except OSError as exc:
            raise OperationAuthorityUnavailableError("machine_authority_create_failed") from exc
        try:
            created_stat = os.fstat(descriptor)
            created_identity = int(created_stat.st_dev), int(created_stat.st_ino)
        finally:
            os.close(descriptor)

        try:
            resolved_path = path.resolve(strict=True)
            current_stat = resolved_path.stat(follow_symlinks=False)
            if (current_stat.st_dev, current_stat.st_ino) != created_identity:
                raise OperationAuthorityBindingError("machine_authority_file_identity_changed")
            observed_security = _observe_security_boundary(verify_security_boundary, resolved_path)
            if observed_security.security_evidence_id != expected_security:
                raise OperationAuthorityBindingError("machine_authority_security_evidence_mismatch")
            if observed_security.generation_evidence_id != expected_generation_evidence:
                raise OperationAuthorityBindingError("machine_authority_generation_evidence_mismatch")
            if observed_security.generation_floor != 0:
                raise OperationAuthorityBindingError("machine_authority_generation_floor_mismatch")
            connection = sqlite3.connect(resolved_path, timeout=30)
            try:
                connection.execute("PRAGMA foreign_keys=ON")
                connection.execute("PRAGMA journal_mode=DELETE")
                connection.execute("PRAGMA busy_timeout=5000")
                connection.executescript(
                    f"""
                    CREATE TABLE authority_metadata (
                      singleton INTEGER PRIMARY KEY CHECK(singleton = 1),
                      authority_id TEXT NOT NULL UNIQUE,
                      security_evidence_id TEXT NOT NULL,
                      file_binding_id TEXT NOT NULL,
                      generation_evidence_id TEXT NOT NULL,
                      provisioning_evidence_id TEXT NOT NULL,
                      schema_version INTEGER NOT NULL CHECK(
                        typeof(schema_version) = 'integer'
                        AND schema_version = {AUTHORITY_SCHEMA_VERSION}
                      ),
                      created_at TEXT NOT NULL,
                      updated_at TEXT NOT NULL
                    );

                    CREATE TABLE machine_global_operation_coordinator (
                      singleton INTEGER PRIMARY KEY CHECK(singleton = 1),
                      coordinator_id TEXT NOT NULL UNIQUE,
                      state TEXT NOT NULL CHECK(state IN ({_COORDINATOR_STATES_SQL})),
                      owner_id TEXT,
                      consumer TEXT CHECK(
                        consumer IS NULL OR consumer IN ({_COORDINATOR_CONSUMERS_SQL})
                      ),
                      generation INTEGER NOT NULL CHECK(
                        typeof(generation) = 'integer'
                        AND generation BETWEEN 0 AND {MAX_COORDINATOR_GENERATION}
                      ),
                      claim_base_generation INTEGER CHECK(
                        claim_base_generation IS NULL OR (
                          typeof(claim_base_generation) = 'integer'
                          AND claim_base_generation BETWEEN 0 AND {MAX_COORDINATOR_GENERATION}
                        )
                      ),
                      active_base_generation INTEGER CHECK(
                        active_base_generation IS NULL OR (
                          typeof(active_base_generation) = 'integer'
                          AND active_base_generation BETWEEN 0 AND {MAX_COORDINATOR_GENERATION}
                        )
                      ),
                      block_base_generation INTEGER CHECK(
                        block_base_generation IS NULL OR (
                          typeof(block_base_generation) = 'integer'
                          AND block_base_generation BETWEEN 0 AND {MAX_COORDINATOR_GENERATION}
                        )
                      ),
                      claim_evidence_id TEXT,
                      active_evidence_id TEXT,
                      block_evidence_id TEXT,
                      updated_at TEXT NOT NULL,
                      CHECK(
                        (state = 'idle' AND owner_id IS NULL AND consumer IS NULL
                          AND claim_base_generation IS NULL AND claim_evidence_id IS NULL
                          AND active_base_generation IS NULL AND block_base_generation IS NULL
                          AND active_evidence_id IS NULL AND block_evidence_id IS NULL)
                        OR
                        (state <> 'idle' AND owner_id IS NOT NULL AND consumer IS NOT NULL
                          AND claim_base_generation IS NOT NULL AND claim_evidence_id IS NOT NULL)
                      ),
                      CHECK(
                        (state = 'claimed' AND active_base_generation IS NULL
                          AND block_base_generation IS NULL
                          AND active_evidence_id IS NULL AND block_evidence_id IS NULL)
                        OR (state = 'active' AND active_base_generation IS NOT NULL
                          AND block_base_generation IS NULL
                          AND active_evidence_id IS NOT NULL AND block_evidence_id IS NULL)
                        OR (state IN ('commit_unknown_blocked','cleanup_blocked')
                          AND block_base_generation IS NOT NULL AND block_evidence_id IS NOT NULL
                          AND ((active_base_generation IS NULL AND active_evidence_id IS NULL)
                            OR (active_base_generation IS NOT NULL AND active_evidence_id IS NOT NULL)))
                        OR state = 'idle'
                      )
                    );
                    """
                )
                now = _utc_now()
                connection.execute(
                    """
                    INSERT INTO authority_metadata(
                      singleton, authority_id, security_evidence_id, file_binding_id,
                      generation_evidence_id, provisioning_evidence_id, schema_version,
                      created_at, updated_at
                    ) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        authority,
                        observed_security.security_evidence_id,
                        observed_security.file_binding_id,
                        observed_security.generation_evidence_id,
                        evidence,
                        AUTHORITY_SCHEMA_VERSION,
                        now,
                        now,
                    ),
                )
                connection.execute(
                    """
                    INSERT INTO machine_global_operation_coordinator(
                      singleton, coordinator_id, state, generation, updated_at
                    ) VALUES (1, ?, 'idle', 0, ?)
                    """,
                    (coordinator, now),
                )
                connection.commit()
            finally:
                connection.close()
            repository = cls(
                path,
                expected_authority_id=authority,
                expected_coordinator_id=coordinator,
                expected_security_evidence_id=expected_security,
                expected_file_binding_id=observed_security.file_binding_id,
                expected_generation_evidence_id=expected_generation_evidence,
                verify_security_boundary=verify_security_boundary,
                advance_generation_floor=advance_generation_floor,
            )
        except Exception as provisioning_error:
            try:
                _cleanup_failed_provision(path, created_identity)
            except OperationAuthorityError as cleanup_error:
                raise cleanup_error from provisioning_error
            raise

        return repository

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        self._verify_security_boundary()
        if self._read_file_identity() != self._file_identity:
            raise OperationAuthorityBindingError("machine_authority_file_identity_changed")
        _reject_linked_authority_sidecars(self.db_path)
        uri = f"{self.db_path.as_uri()}?mode=rw"
        try:
            connection = sqlite3.connect(uri, uri=True, timeout=30)
        except sqlite3.Error as exc:
            raise OperationAuthorityUnavailableError("machine_authority_open_failed") from exc
        try:
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute("PRAGMA busy_timeout=5000")
            if self._read_file_identity() != self._file_identity:
                raise OperationAuthorityBindingError("machine_authority_file_identity_changed")
            journal_mode = str(connection.execute("PRAGMA journal_mode").fetchone()[0]).lower()
            if journal_mode != AUTHORITY_JOURNAL_MODE:
                raise OperationAuthorityBindingError("machine_authority_journal_mode_mismatch")
            yield connection
            connection.commit()
        except sqlite3.Error as exc:
            try:
                connection.rollback()
            except sqlite3.Error:
                pass
            raise OperationAuthorityUnavailableError("machine_authority_connection_failed") from exc
        except Exception:
            try:
                connection.rollback()
            except sqlite3.Error:
                pass
            raise
        finally:
            connection.close()

    def get_snapshot(self) -> CoordinatorSnapshot:
        with self._connect() as connection:
            return self._validate_binding(connection)

    def claim(
        self,
        *,
        expected_generation: int,
        owner_id: str,
        consumer: str,
        claim_evidence_id: str,
    ) -> CoordinatorTransitionResult:
        owner = _required_identifier(owner_id, "owner_id")
        normalized_consumer = self._consumer(consumer)
        evidence = _required_identifier(claim_evidence_id, "claim_evidence_id")
        expected_generation = _required_transition_generation(expected_generation)

        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            current = self._validate_binding(connection)
            if current.state in {"commit_unknown_blocked", "cleanup_blocked"}:
                return CoordinatorTransitionResult(False, False, "coordinator_blocked", current)
            if self._same_claim(current, expected_generation, owner, normalized_consumer, evidence):
                return CoordinatorTransitionResult(False, True, None, current)
            if current.state != "idle":
                return CoordinatorTransitionResult(False, False, "coordinator_not_idle", current)
            if current.generation != expected_generation:
                return CoordinatorTransitionResult(False, False, "coordinator_generation_mismatch", current)

            now = _utc_now()
            updated = connection.execute(
                """
                UPDATE machine_global_operation_coordinator
                SET state = 'claimed', owner_id = ?, consumer = ?, generation = generation + 1,
                    claim_base_generation = ?, active_base_generation = NULL,
                    block_base_generation = NULL, claim_evidence_id = ?, active_evidence_id = NULL,
                    block_evidence_id = NULL, updated_at = ?
                WHERE singleton = 1 AND coordinator_id = ? AND state = 'idle'
                  AND owner_id IS NULL AND consumer IS NULL AND generation = ?
                """,
                (
                    owner,
                    normalized_consumer,
                    expected_generation,
                    evidence,
                    now,
                    self.expected_coordinator_id,
                    expected_generation,
                ),
            )
            snapshot = self._validate_binding(connection, verify_generation_floor=False)
            if updated.rowcount != 1:
                current = self._validate_binding(connection)
                return CoordinatorTransitionResult(False, False, "coordinator_claim_lost", current)
            self._advance_external_generation_floor(expected_generation, snapshot.generation)
            self._validate_binding(connection)
            return CoordinatorTransitionResult(True, False, None, snapshot)

    def activate(
        self,
        *,
        expected_generation: int,
        owner_id: str,
        consumer: str,
        active_evidence_id: str,
    ) -> CoordinatorTransitionResult:
        owner = _required_identifier(owner_id, "owner_id")
        normalized_consumer = self._consumer(consumer)
        evidence = _required_identifier(active_evidence_id, "active_evidence_id")
        return self._advance_owned(
            expected_state="claimed",
            next_state="active",
            expected_generation=expected_generation,
            owner_id=owner,
            consumer=normalized_consumer,
            evidence_id=evidence,
        )

    def mark_commit_unknown(
        self,
        *,
        expected_generation: int,
        owner_id: str,
        consumer: str,
        block_evidence_id: str,
    ) -> CoordinatorTransitionResult:
        return self._mark_blocked(
            next_state="commit_unknown_blocked",
            expected_generation=expected_generation,
            owner_id=owner_id,
            consumer=consumer,
            block_evidence_id=block_evidence_id,
        )

    def mark_cleanup_blocked(
        self,
        *,
        expected_generation: int,
        owner_id: str,
        consumer: str,
        block_evidence_id: str,
    ) -> CoordinatorTransitionResult:
        return self._mark_blocked(
            next_state="cleanup_blocked",
            expected_generation=expected_generation,
            owner_id=owner_id,
            consumer=consumer,
            block_evidence_id=block_evidence_id,
        )

    def _mark_blocked(
        self,
        *,
        next_state: str,
        expected_generation: int,
        owner_id: str,
        consumer: str,
        block_evidence_id: str,
    ) -> CoordinatorTransitionResult:
        owner = _required_identifier(owner_id, "owner_id")
        normalized_consumer = self._consumer(consumer)
        evidence = _required_identifier(block_evidence_id, "block_evidence_id")
        expected_generation = _required_transition_generation(expected_generation)

        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            current = self._validate_binding(connection)
            if (
                current.state == next_state
                and current.owner_id == owner
                and current.consumer == normalized_consumer
                and current.block_base_generation == expected_generation
                and current.block_evidence_id == evidence
            ):
                return CoordinatorTransitionResult(False, True, None, current)
            if current.owner_id != owner or current.consumer != normalized_consumer:
                return CoordinatorTransitionResult(False, False, "coordinator_owner_mismatch", current)
            if current.generation != expected_generation:
                return CoordinatorTransitionResult(False, False, "coordinator_generation_mismatch", current)
            if current.state not in {"claimed", "active"}:
                return CoordinatorTransitionResult(False, False, "coordinator_state_mismatch", current)

            now = _utc_now()
            updated = connection.execute(
                """
                UPDATE machine_global_operation_coordinator
                SET state = ?, generation = generation + 1, block_base_generation = ?,
                    block_evidence_id = ?, updated_at = ?
                WHERE singleton = 1 AND coordinator_id = ? AND state IN ('claimed','active')
                  AND owner_id = ? AND consumer = ? AND generation = ?
                """,
                (
                    next_state,
                    expected_generation,
                    evidence,
                    now,
                    self.expected_coordinator_id,
                    owner,
                    normalized_consumer,
                    expected_generation,
                ),
            )
            snapshot = self._validate_binding(connection, verify_generation_floor=False)
            if updated.rowcount != 1:
                current = self._validate_binding(connection)
                return CoordinatorTransitionResult(False, False, "coordinator_transition_lost", current)
            self._advance_external_generation_floor(expected_generation, snapshot.generation)
            self._validate_binding(connection)
            return CoordinatorTransitionResult(True, False, None, snapshot)

    def _advance_owned(
        self,
        *,
        expected_state: str,
        next_state: str,
        expected_generation: int,
        owner_id: str,
        consumer: str,
        evidence_id: str,
    ) -> CoordinatorTransitionResult:
        expected_generation = _required_transition_generation(expected_generation)

        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            current = self._validate_binding(connection)
            if (
                current.state == next_state
                and current.owner_id == owner_id
                and current.consumer == consumer
                and current.active_base_generation == expected_generation
                and current.active_evidence_id == evidence_id
            ):
                return CoordinatorTransitionResult(False, True, None, current)
            if current.state in {"commit_unknown_blocked", "cleanup_blocked"}:
                return CoordinatorTransitionResult(False, False, "coordinator_blocked", current)
            if current.owner_id != owner_id or current.consumer != consumer:
                return CoordinatorTransitionResult(False, False, "coordinator_owner_mismatch", current)
            if current.generation != expected_generation:
                return CoordinatorTransitionResult(False, False, "coordinator_generation_mismatch", current)
            if current.state != expected_state:
                return CoordinatorTransitionResult(False, False, "coordinator_state_mismatch", current)

            now = _utc_now()
            updated = connection.execute(
                """
                UPDATE machine_global_operation_coordinator
                SET state = ?, generation = generation + 1, active_base_generation = ?,
                    active_evidence_id = ?, updated_at = ?
                WHERE singleton = 1 AND coordinator_id = ? AND state = ?
                  AND owner_id = ? AND consumer = ? AND generation = ?
                """,
                (
                    next_state,
                    expected_generation,
                    evidence_id,
                    now,
                    self.expected_coordinator_id,
                    expected_state,
                    owner_id,
                    consumer,
                    expected_generation,
                ),
            )
            snapshot = self._validate_binding(connection, verify_generation_floor=False)
            if updated.rowcount != 1:
                current = self._validate_binding(connection)
                return CoordinatorTransitionResult(False, False, "coordinator_transition_lost", current)
            self._advance_external_generation_floor(expected_generation, snapshot.generation)
            self._validate_binding(connection)
            return CoordinatorTransitionResult(True, False, None, snapshot)

    def _validate_binding(
        self,
        connection: sqlite3.Connection,
        *,
        verify_generation_floor: bool = True,
    ) -> CoordinatorSnapshot:
        try:
            metadata = connection.execute(
                """
                SELECT authority_id, security_evidence_id, file_binding_id,
                       generation_evidence_id, schema_version
                FROM authority_metadata
                WHERE singleton = 1
                """
            ).fetchone()
            row = connection.execute(
                "SELECT * FROM machine_global_operation_coordinator WHERE singleton = 1"
            ).fetchone()
        except sqlite3.Error as exc:
            raise OperationAuthorityBindingError("machine_authority_schema_invalid") from exc
        if metadata is None or row is None:
            raise OperationAuthorityBindingError("machine_authority_schema_incomplete")
        if (
            type(metadata["schema_version"]) is not int
            or metadata["schema_version"] != AUTHORITY_SCHEMA_VERSION
        ):
            raise OperationAuthorityBindingError("machine_authority_schema_version_mismatch")
        if str(metadata["authority_id"]) != self.expected_authority_id:
            raise OperationAuthorityBindingError("machine_authority_id_mismatch")
        if str(metadata["security_evidence_id"]) != self.expected_security_evidence_id:
            raise OperationAuthorityBindingError("machine_authority_security_evidence_mismatch")
        if str(metadata["file_binding_id"]) != self.expected_file_binding_id:
            raise OperationAuthorityBindingError("machine_authority_file_binding_mismatch")
        if str(metadata["generation_evidence_id"]) != self.expected_generation_evidence_id:
            raise OperationAuthorityBindingError("machine_authority_generation_evidence_mismatch")
        if str(row["coordinator_id"]) != self.expected_coordinator_id:
            raise OperationAuthorityBindingError("machine_coordinator_id_mismatch")
        state = str(row["state"])
        consumer = (
            None
            if row["consumer"] is None
            else _stored_identifier(row["consumer"], "machine_coordinator_consumer")
        )
        if state not in COORDINATOR_STATES or (consumer is not None and consumer not in COORDINATOR_CONSUMERS):
            raise OperationAuthorityBindingError("machine_coordinator_state_invalid")
        active_evidence = (
            None
            if row["active_evidence_id"] is None
            else _stored_identifier(
                row["active_evidence_id"],
                "machine_coordinator_active_evidence_id",
            )
        )
        block_evidence = (
            None
            if row["block_evidence_id"] is None
            else _stored_identifier(
                row["block_evidence_id"],
                "machine_coordinator_block_evidence_id",
            )
        )
        owner = (
            None
            if row["owner_id"] is None
            else _stored_identifier(row["owner_id"], "machine_coordinator_owner_id")
        )
        claim_evidence = (
            None
            if row["claim_evidence_id"] is None
            else _stored_identifier(
                row["claim_evidence_id"],
                "machine_coordinator_claim_evidence_id",
            )
        )
        generation = _strict_generation(row["generation"], "machine_coordinator_generation")
        claim_base_generation = (
            None
            if row["claim_base_generation"] is None
            else _strict_generation(
                row["claim_base_generation"],
                "machine_coordinator_claim_base_generation",
            )
        )
        active_base_generation = (
            None
            if row["active_base_generation"] is None
            else _strict_generation(
                row["active_base_generation"],
                "machine_coordinator_active_base_generation",
            )
        )
        block_base_generation = (
            None
            if row["block_base_generation"] is None
            else _strict_generation(
                row["block_base_generation"],
                "machine_coordinator_block_base_generation",
            )
        )
        if (
            generation < 0
            or (
                state == "idle"
                and any(
                    value is not None
                    for value in (owner, consumer, claim_base_generation, claim_evidence)
                )
            )
            or (
                state != "idle"
                and any(
                    value is None
                    for value in (owner, consumer, claim_base_generation, claim_evidence)
                )
            )
            or (
                state == "idle"
                and any(
                    value is not None
                    for value in (
                        active_base_generation,
                        block_base_generation,
                        active_evidence,
                        block_evidence,
                    )
                )
            )
            or (
                state == "claimed"
                and any(
                    value is not None
                    for value in (
                        active_base_generation,
                        block_base_generation,
                        active_evidence,
                        block_evidence,
                    )
                )
            )
            or (
                state == "active"
                and (
                    active_base_generation is None
                    or active_evidence is None
                    or block_base_generation is not None
                    or block_evidence is not None
                )
            )
            or (
                state in {"commit_unknown_blocked", "cleanup_blocked"}
                and (
                    block_base_generation is None
                    or block_evidence is None
                    or ((active_base_generation is None) != (active_evidence is None))
                )
            )
            or (
                state == "claimed"
                and generation != claim_base_generation + 1
            )
            or (
                state == "active"
                and (
                    active_base_generation != claim_base_generation + 1
                    or generation != active_base_generation + 1
                )
            )
            or (
                state in {"commit_unknown_blocked", "cleanup_blocked"}
                and (
                    generation != block_base_generation + 1
                    or (
                        active_base_generation is None
                        and block_base_generation != claim_base_generation + 1
                    )
                    or (
                        active_base_generation is not None
                        and (
                            active_base_generation != claim_base_generation + 1
                            or block_base_generation != active_base_generation + 1
                        )
                    )
                )
            )
        ):
            raise OperationAuthorityBindingError("machine_coordinator_evidence_state_invalid")
        if verify_generation_floor:
            observed_security = self._verify_security_boundary()
            if observed_security.generation_floor != generation:
                raise OperationAuthorityBindingError("machine_authority_generation_floor_mismatch")
        return CoordinatorSnapshot(
            coordinator_id=str(row["coordinator_id"]),
            state=state,
            owner_id=owner,
            consumer=consumer,
            generation=generation,
            claim_base_generation=claim_base_generation,
            active_base_generation=active_base_generation,
            block_base_generation=block_base_generation,
            claim_evidence_id=claim_evidence,
            active_evidence_id=active_evidence,
            block_evidence_id=block_evidence,
            updated_at=str(row["updated_at"]),
        )

    @staticmethod
    def _same_claim(
        snapshot: CoordinatorSnapshot,
        expected_generation: int,
        owner_id: str,
        consumer: str,
        claim_evidence_id: str,
    ) -> bool:
        return (
            snapshot.state in {"claimed", "active"}
            and snapshot.owner_id == owner_id
            and snapshot.consumer == consumer
            and snapshot.claim_base_generation == expected_generation
            and snapshot.claim_evidence_id == claim_evidence_id
        )

    @staticmethod
    def _consumer(value: str) -> str:
        normalized = value.strip()
        if normalized not in COORDINATOR_CONSUMERS:
            raise ValueError("coordinator_consumer_invalid")
        return normalized

    def _verify_security_boundary(self) -> AuthoritySecurityAttestation:
        observed = _observe_security_boundary(self.verify_security_boundary, self.db_path)
        if observed.security_evidence_id != self.expected_security_evidence_id:
            raise OperationAuthorityBindingError("machine_authority_security_evidence_mismatch")
        if observed.file_binding_id != self.expected_file_binding_id:
            raise OperationAuthorityBindingError("machine_authority_file_binding_mismatch")
        if observed.generation_evidence_id != self.expected_generation_evidence_id:
            raise OperationAuthorityBindingError("machine_authority_generation_evidence_mismatch")
        return observed

    def _advance_external_generation_floor(
        self,
        expected_generation: int,
        next_generation: int,
    ) -> None:
        try:
            self.advance_generation_floor(self.db_path, expected_generation, next_generation)
        except OperationAuthorityError:
            raise
        except Exception as exc:
            raise OperationAuthorityUnavailableError(
                "machine_authority_generation_floor_advance_failed"
            ) from exc
        observed = self._verify_security_boundary()
        if observed.generation_floor != next_generation:
            raise OperationAuthorityBindingError("machine_authority_generation_floor_mismatch")

    def _read_file_identity(self) -> tuple[int, int]:
        try:
            file_stat = self.db_path.stat(follow_symlinks=False)
        except OSError as exc:
            raise OperationAuthorityUnavailableError("machine_authority_path_unreadable") from exc
        return int(file_stat.st_dev), int(file_stat.st_ino)
