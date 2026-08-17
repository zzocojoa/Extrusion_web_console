from __future__ import annotations

import multiprocessing
import shutil
import sqlite3
import stat
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import pytest

import backend.app.core.machine_authority as machine_authority
import backend.app.db.operation_authority_repository as authority_repository
from backend.app.core.machine_authority import (
    MACHINE_AUTHORITY_RELATIVE_PATH,
    MachineAuthorityLocationError,
    resolve_machine_authority_db_path,
)
from backend.app.db.operation_authority_repository import (
    AuthoritySecurityAttestation,
    COORDINATOR_CONSUMERS,
    OperationAuthorityBindingError,
    OperationAuthorityRepository,
    OperationAuthorityUnavailableError,
)


AUTHORITY_ID = "authority_7a93bd53a43a4f04"
COORDINATOR_ID = "coordinator_64c6ba684d084352"
SECURITY_EVIDENCE_ID = "security_acl_32ff09b74d6d4d79"
PARENT_SECURITY_EVIDENCE_ID = "security_parent_acl_98816fd684bd4ad3"
GENERATION_EVIDENCE_ID = "security_generation_floor_ebbc25ffb2ea411f"


def observed_file_binding(path: Path) -> str:
    file_stat = path.stat(follow_symlinks=False)
    return f"file_{int(file_stat.st_dev):x}_{int(file_stat.st_ino):x}"


def generation_floor_path(path: Path) -> Path:
    return path.with_name(f"{path.name}.test-generation-floor.db")


def read_test_generation_floor(path: Path) -> int:
    with sqlite3.connect(generation_floor_path(path), timeout=30) as connection:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS generation_floor(singleton INTEGER PRIMARY KEY, value INTEGER NOT NULL)"
        )
        connection.execute(
            "INSERT OR IGNORE INTO generation_floor(singleton, value) VALUES (1, 0)"
        )
        return int(
            connection.execute(
                "SELECT value FROM generation_floor WHERE singleton = 1"
            ).fetchone()[0]
        )


def verify_test_security(path: Path) -> AuthoritySecurityAttestation:
    return AuthoritySecurityAttestation(
        security_evidence_id=SECURITY_EVIDENCE_ID,
        file_binding_id=observed_file_binding(path),
        generation_evidence_id=GENERATION_EVIDENCE_ID,
        generation_floor=read_test_generation_floor(path),
    )


def verify_test_parent(_: Path) -> str:
    return PARENT_SECURITY_EVIDENCE_ID


def advance_test_generation_floor(path: Path, expected: int, next_value: int) -> None:
    with sqlite3.connect(generation_floor_path(path), timeout=30) as connection:
        connection.execute("BEGIN IMMEDIATE")
        updated = connection.execute(
            "UPDATE generation_floor SET value = ? WHERE singleton = 1 AND value = ?",
            (next_value, expected),
        )
        if updated.rowcount != 1:
            raise RuntimeError("test_generation_floor_cas_lost")


def provision(tmp_path: Path) -> OperationAuthorityRepository:
    return OperationAuthorityRepository.provision(
        tmp_path / "operation_authority.db",
        authority_id=AUTHORITY_ID,
        coordinator_id=COORDINATOR_ID,
        initial_evidence_id="evidence_provisioned_7ab5",
        expected_parent_security_evidence_id=PARENT_SECURITY_EVIDENCE_ID,
        expected_security_evidence_id=SECURITY_EVIDENCE_ID,
        expected_generation_evidence_id=GENERATION_EVIDENCE_ID,
        verify_provisioning_parent=verify_test_parent,
        verify_security_boundary=verify_test_security,
        advance_generation_floor=advance_test_generation_floor,
    )


def reopen(
    path: Path,
    *,
    expected_file_binding_id: str | None = None,
) -> OperationAuthorityRepository:
    return OperationAuthorityRepository(
        path,
        expected_authority_id=AUTHORITY_ID,
        expected_coordinator_id=COORDINATOR_ID,
        expected_security_evidence_id=SECURITY_EVIDENCE_ID,
        expected_file_binding_id=(
            expected_file_binding_id
            or (observed_file_binding(path) if path.exists() else "file_missing_expected")
        ),
        expected_generation_evidence_id=GENERATION_EVIDENCE_ID,
        verify_security_boundary=verify_test_security,
        advance_generation_floor=advance_test_generation_floor,
    )


def claim_in_process(
    path: str,
    expected_file_binding_id: str,
    owner_id: str,
    consumer: str,
    start_barrier: multiprocessing.synchronize.Barrier,
    result_queue: multiprocessing.queues.Queue,
) -> None:
    repository = reopen(Path(path), expected_file_binding_id=expected_file_binding_id)
    start_barrier.wait(timeout=10)
    result = repository.claim(
        expected_generation=0,
        owner_id=owner_id,
        consumer=consumer,
        claim_evidence_id=f"evidence_{owner_id}",
    )
    result_queue.put((result.applied, result.reason, result.snapshot.owner_id))


def test_machine_authority_path_uses_known_folder_not_process_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ProgramData", r"D:\attacker")
    monkeypatch.setenv("EWC_STATE_DB_PATH", r"D:\other-user\state.db")
    monkeypatch.setenv("EWC_CONFIG_FILE_PATH", r"D:\package\config.json")
    monkeypatch.setenv("EWC_MACHINE_AUTHORITY_DB_PATH", r"D:\attacker\authority.db")
    monkeypatch.setattr(
        machine_authority,
        "_resolve_program_data_known_folder",
        lambda: Path(r"C:\ProgramData"),
    )

    resolved = resolve_machine_authority_db_path(platform_name="nt")

    assert resolved == Path(r"C:\ProgramData") / MACHINE_AUTHORITY_RELATIVE_PATH


def test_machine_authority_path_requires_windows() -> None:
    with pytest.raises(MachineAuthorityLocationError, match="machine_authority_requires_windows"):
        resolve_machine_authority_db_path(platform_name="posix")


def test_machine_authority_path_rejects_relative_known_folder(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        machine_authority,
        "_resolve_program_data_known_folder",
        lambda: Path("relative"),
    )

    with pytest.raises(
        MachineAuthorityLocationError,
        match="machine_authority_program_data_not_absolute",
    ):
        resolve_machine_authority_db_path(platform_name="nt")


def test_repository_never_auto_creates_missing_authority(tmp_path: Path) -> None:
    path = tmp_path / "missing.db"

    with pytest.raises(OperationAuthorityUnavailableError, match="machine_authority_not_provisioned"):
        reopen(path)

    assert not path.exists()


def test_provision_is_exclusive_and_requires_preexisting_parent(tmp_path: Path) -> None:
    repository = provision(tmp_path)
    path = Path(repository.db_path)

    with pytest.raises(OperationAuthorityUnavailableError, match="machine_authority_already_exists"):
        OperationAuthorityRepository.provision(
            path,
            authority_id=AUTHORITY_ID,
            coordinator_id=COORDINATOR_ID,
            initial_evidence_id="evidence_second",
            expected_parent_security_evidence_id=PARENT_SECURITY_EVIDENCE_ID,
            expected_security_evidence_id=SECURITY_EVIDENCE_ID,
            expected_generation_evidence_id=GENERATION_EVIDENCE_ID,
            verify_provisioning_parent=verify_test_parent,
            verify_security_boundary=verify_test_security,
            advance_generation_floor=advance_test_generation_floor,
        )
    with pytest.raises(OperationAuthorityUnavailableError, match="machine_authority_parent_missing"):
        OperationAuthorityRepository.provision(
            tmp_path / "absent" / "authority.db",
            authority_id=AUTHORITY_ID,
            coordinator_id=COORDINATOR_ID,
            initial_evidence_id="evidence_absent_parent",
            expected_parent_security_evidence_id=PARENT_SECURITY_EVIDENCE_ID,
            expected_security_evidence_id=SECURITY_EVIDENCE_ID,
            expected_generation_evidence_id=GENERATION_EVIDENCE_ID,
            verify_provisioning_parent=verify_test_parent,
            verify_security_boundary=verify_test_security,
            advance_generation_floor=advance_test_generation_floor,
        )


@pytest.mark.parametrize("suffix", ("-journal", "-wal", "-shm"))
def test_provision_rejects_and_preserves_preexisting_regular_sidecar(
    tmp_path: Path,
    suffix: str,
) -> None:
    path = tmp_path / "operation_authority.db"
    sidecar = Path(f"{path}{suffix}")
    original_content = b"preexisting-sidecar-must-not-be-consumed-or-deleted"
    sidecar.write_bytes(original_content)

    with pytest.raises(
        OperationAuthorityUnavailableError,
        match="machine_authority_sidecar_already_exists",
    ):
        OperationAuthorityRepository.provision(
            path,
            authority_id=AUTHORITY_ID,
            coordinator_id=COORDINATOR_ID,
            initial_evidence_id="evidence_provisioned",
            expected_parent_security_evidence_id=PARENT_SECURITY_EVIDENCE_ID,
            expected_security_evidence_id=SECURITY_EVIDENCE_ID,
            expected_generation_evidence_id=GENERATION_EVIDENCE_ID,
            verify_provisioning_parent=verify_test_parent,
            verify_security_boundary=verify_test_security,
            advance_generation_floor=advance_test_generation_floor,
        )

    assert not path.exists()
    assert sidecar.read_bytes() == original_content


def test_provision_verifies_parent_before_create_and_file_after_create(tmp_path: Path) -> None:
    path = tmp_path / "operation_authority.db"
    parent_observations: list[bool] = []
    file_observations: list[bool] = []

    def parent_verifier(candidate: Path) -> str:
        parent_observations.append(candidate.exists())
        return PARENT_SECURITY_EVIDENCE_ID

    def file_verifier(candidate: Path) -> AuthoritySecurityAttestation:
        file_observations.append(candidate.exists())
        return verify_test_security(candidate)

    OperationAuthorityRepository.provision(
        path,
        authority_id=AUTHORITY_ID,
        coordinator_id=COORDINATOR_ID,
        initial_evidence_id="evidence_provisioned",
        expected_parent_security_evidence_id=PARENT_SECURITY_EVIDENCE_ID,
        expected_security_evidence_id=SECURITY_EVIDENCE_ID,
        expected_generation_evidence_id=GENERATION_EVIDENCE_ID,
        verify_provisioning_parent=parent_verifier,
        verify_security_boundary=file_verifier,
        advance_generation_floor=advance_test_generation_floor,
    )

    assert parent_observations == [False]
    assert file_observations and all(file_observations)


def test_provision_security_mismatch_creates_no_file(tmp_path: Path) -> None:
    path = tmp_path / "operation_authority.db"

    with pytest.raises(OperationAuthorityBindingError, match="machine_authority_security_evidence_mismatch"):
        OperationAuthorityRepository.provision(
            path,
            authority_id=AUTHORITY_ID,
            coordinator_id=COORDINATOR_ID,
            initial_evidence_id="evidence_provisioned",
            expected_parent_security_evidence_id=PARENT_SECURITY_EVIDENCE_ID,
            expected_security_evidence_id=SECURITY_EVIDENCE_ID,
            expected_generation_evidence_id=GENERATION_EVIDENCE_ID,
            verify_provisioning_parent=verify_test_parent,
            verify_security_boundary=lambda candidate: AuthoritySecurityAttestation(
                security_evidence_id="security_substituted",
                file_binding_id=observed_file_binding(candidate),
                generation_evidence_id=GENERATION_EVIDENCE_ID,
                generation_floor=read_test_generation_floor(candidate),
            ),
            advance_generation_floor=advance_test_generation_floor,
        )

    assert not path.exists()


def test_provision_final_validation_failure_removes_owned_database(tmp_path: Path) -> None:
    path = tmp_path / "operation_authority.db"
    observations = 0

    def verifier(candidate: Path) -> AuthoritySecurityAttestation:
        nonlocal observations
        observations += 1
        return AuthoritySecurityAttestation(
            security_evidence_id=(
                SECURITY_EVIDENCE_ID if observations == 1 else "security_substituted"
            ),
            file_binding_id=observed_file_binding(candidate),
            generation_evidence_id=GENERATION_EVIDENCE_ID,
            generation_floor=read_test_generation_floor(candidate),
        )

    with pytest.raises(
        OperationAuthorityBindingError,
        match="machine_authority_security_evidence_mismatch",
    ):
        OperationAuthorityRepository.provision(
            path,
            authority_id=AUTHORITY_ID,
            coordinator_id=COORDINATOR_ID,
            initial_evidence_id="evidence_provisioned",
            expected_parent_security_evidence_id=PARENT_SECURITY_EVIDENCE_ID,
            expected_security_evidence_id=SECURITY_EVIDENCE_ID,
            expected_generation_evidence_id=GENERATION_EVIDENCE_ID,
            verify_provisioning_parent=verify_test_parent,
            verify_security_boundary=verifier,
            advance_generation_floor=advance_test_generation_floor,
        )

    assert observations == 2
    assert not path.exists()


def test_provision_parent_security_mismatch_performs_zero_file_write(tmp_path: Path) -> None:
    path = tmp_path / "operation_authority.db"

    with pytest.raises(
        OperationAuthorityBindingError,
        match="machine_authority_parent_security_evidence_mismatch",
    ):
        OperationAuthorityRepository.provision(
            path,
            authority_id=AUTHORITY_ID,
            coordinator_id=COORDINATOR_ID,
            initial_evidence_id="evidence_provisioned",
            expected_parent_security_evidence_id=PARENT_SECURITY_EVIDENCE_ID,
            expected_security_evidence_id=SECURITY_EVIDENCE_ID,
            expected_generation_evidence_id=GENERATION_EVIDENCE_ID,
            verify_provisioning_parent=lambda _: "security_parent_substituted",
            verify_security_boundary=verify_test_security,
            advance_generation_floor=advance_test_generation_floor,
        )

    assert not path.exists()


def test_repository_rejects_symlinked_authority_file(tmp_path: Path) -> None:
    real_dir = tmp_path / "real"
    real_dir.mkdir()
    real_path = Path(provision(real_dir).db_path)
    link_path = tmp_path / "authority-link.db"
    try:
        link_path.symlink_to(real_path)
    except OSError:
        pytest.skip("symlink creation unavailable")

    with pytest.raises(OperationAuthorityUnavailableError, match="machine_authority_path_has_link_component"):
        reopen(link_path)


def test_provision_rejects_symlinked_parent_directory(tmp_path: Path) -> None:
    real_parent = tmp_path / "real-parent"
    real_parent.mkdir()
    linked_parent = tmp_path / "linked-parent"
    try:
        linked_parent.symlink_to(real_parent, target_is_directory=True)
    except OSError:
        pytest.skip("directory symlink creation unavailable")

    with pytest.raises(OperationAuthorityUnavailableError, match="machine_authority_path_has_link_component"):
        OperationAuthorityRepository.provision(
            linked_parent / "operation_authority.db",
            authority_id=AUTHORITY_ID,
            coordinator_id=COORDINATOR_ID,
            initial_evidence_id="evidence_linked_parent",
            expected_parent_security_evidence_id=PARENT_SECURITY_EVIDENCE_ID,
            expected_security_evidence_id=SECURITY_EVIDENCE_ID,
            expected_generation_evidence_id=GENERATION_EVIDENCE_ID,
            verify_provisioning_parent=verify_test_parent,
            verify_security_boundary=verify_test_security,
            advance_generation_floor=advance_test_generation_floor,
        )


def test_reparse_attribute_is_rejected_without_platform_specific_link_privileges() -> None:
    class FakeReparsePath:
        parents = ()

        @staticmethod
        def is_symlink() -> bool:
            return False

        @staticmethod
        def stat(*, follow_symlinks: bool):
            assert follow_symlinks is False
            return SimpleNamespace(st_file_attributes=stat.FILE_ATTRIBUTE_REPARSE_POINT)

    with pytest.raises(OperationAuthorityUnavailableError, match="machine_authority_path_has_reparse_component"):
        authority_repository._reject_link_or_reparse_components(FakeReparsePath())


@pytest.mark.parametrize(
    ("expected_authority_id", "expected_coordinator_id", "reason"),
    [
        ("authority_substituted", COORDINATOR_ID, "machine_authority_id_mismatch"),
        (AUTHORITY_ID, "coordinator_substituted", "machine_coordinator_id_mismatch"),
    ],
)
def test_repository_rejects_substituted_trust_bindings(
    tmp_path: Path,
    expected_authority_id: str,
    expected_coordinator_id: str,
    reason: str,
) -> None:
    path = Path(provision(tmp_path).db_path)

    with pytest.raises(OperationAuthorityBindingError, match=reason):
        OperationAuthorityRepository(
            path,
            expected_authority_id=expected_authority_id,
            expected_coordinator_id=expected_coordinator_id,
            expected_security_evidence_id=SECURITY_EVIDENCE_ID,
            expected_file_binding_id=observed_file_binding(path),
            expected_generation_evidence_id=GENERATION_EVIDENCE_ID,
            verify_security_boundary=verify_test_security,
            advance_generation_floor=advance_test_generation_floor,
        )


def test_repository_rejects_missing_or_substituted_security_attestation(tmp_path: Path) -> None:
    path = Path(provision(tmp_path).db_path)

    with pytest.raises(OperationAuthorityBindingError, match="machine_authority_security_evidence_mismatch"):
        OperationAuthorityRepository(
            path,
            expected_authority_id=AUTHORITY_ID,
            expected_coordinator_id=COORDINATOR_ID,
            expected_security_evidence_id=SECURITY_EVIDENCE_ID,
            expected_file_binding_id=observed_file_binding(path),
            expected_generation_evidence_id=GENERATION_EVIDENCE_ID,
            verify_security_boundary=lambda candidate: AuthoritySecurityAttestation(
                security_evidence_id="security_substituted",
                file_binding_id=observed_file_binding(candidate),
                generation_evidence_id=GENERATION_EVIDENCE_ID,
                generation_floor=read_test_generation_floor(candidate),
            ),
            advance_generation_floor=advance_test_generation_floor,
        )


def test_open_repository_revalidates_security_before_every_operation(tmp_path: Path) -> None:
    observed = {"evidence_id": SECURITY_EVIDENCE_ID}

    def verifier(candidate: Path) -> AuthoritySecurityAttestation:
        return AuthoritySecurityAttestation(
            security_evidence_id=observed["evidence_id"],
            file_binding_id=observed_file_binding(candidate),
            generation_evidence_id=GENERATION_EVIDENCE_ID,
            generation_floor=read_test_generation_floor(candidate),
        )

    repository = OperationAuthorityRepository.provision(
        tmp_path / "operation_authority.db",
        authority_id=AUTHORITY_ID,
        coordinator_id=COORDINATOR_ID,
        initial_evidence_id="evidence_provisioned_7ab5",
        expected_parent_security_evidence_id=PARENT_SECURITY_EVIDENCE_ID,
        expected_security_evidence_id=SECURITY_EVIDENCE_ID,
        expected_generation_evidence_id=GENERATION_EVIDENCE_ID,
        verify_provisioning_parent=verify_test_parent,
        verify_security_boundary=verifier,
        advance_generation_floor=advance_test_generation_floor,
    )
    initial = repository.get_snapshot()
    observed["evidence_id"] = "security_substituted"

    with pytest.raises(OperationAuthorityBindingError, match="machine_authority_security_evidence_mismatch"):
        repository.claim(
            expected_generation=0,
            owner_id="operation_a",
            consumer="start",
            claim_evidence_id="evidence_claim_a",
        )

    observed["evidence_id"] = SECURITY_EVIDENCE_ID
    assert repository.get_snapshot() == initial


def test_open_repository_revalidates_file_binding_before_every_operation(tmp_path: Path) -> None:
    repository = provision(tmp_path)
    path = Path(repository.db_path)
    expected_file_binding_id = repository.expected_file_binding_id
    observed = {"file_binding_id": expected_file_binding_id}

    def verifier(_: Path) -> AuthoritySecurityAttestation:
        return AuthoritySecurityAttestation(
            security_evidence_id=SECURITY_EVIDENCE_ID,
            file_binding_id=observed["file_binding_id"],
            generation_evidence_id=GENERATION_EVIDENCE_ID,
            generation_floor=read_test_generation_floor(path),
        )

    reopened = OperationAuthorityRepository(
        path,
        expected_authority_id=AUTHORITY_ID,
        expected_coordinator_id=COORDINATOR_ID,
        expected_security_evidence_id=SECURITY_EVIDENCE_ID,
        expected_file_binding_id=expected_file_binding_id,
        expected_generation_evidence_id=GENERATION_EVIDENCE_ID,
        verify_security_boundary=verifier,
        advance_generation_floor=advance_test_generation_floor,
    )
    initial = reopened.get_snapshot()
    observed["file_binding_id"] = "file_substituted"

    with pytest.raises(OperationAuthorityBindingError, match="machine_authority_file_binding_mismatch"):
        reopened.claim(
            expected_generation=0,
            owner_id="operation_a",
            consumer="start",
            claim_evidence_id="evidence_claim_a",
        )

    observed["file_binding_id"] = expected_file_binding_id
    assert reopened.get_snapshot() == initial


def test_repository_rejects_security_verifier_failure(tmp_path: Path) -> None:
    path = Path(provision(tmp_path).db_path)

    def failed_verifier(_: Path) -> str:
        raise OSError("security descriptor unavailable")

    with pytest.raises(
        OperationAuthorityUnavailableError,
        match="machine_authority_security_verification_failed",
    ):
        OperationAuthorityRepository(
            path,
            expected_authority_id=AUTHORITY_ID,
            expected_coordinator_id=COORDINATOR_ID,
            expected_security_evidence_id=SECURITY_EVIDENCE_ID,
            expected_file_binding_id=observed_file_binding(path),
            expected_generation_evidence_id=GENERATION_EVIDENCE_ID,
            verify_security_boundary=failed_verifier,
            advance_generation_floor=advance_test_generation_floor,
        )


def test_claim_and_activate_use_monotonic_owner_bound_generations(tmp_path: Path) -> None:
    repository = provision(tmp_path)

    claimed = repository.claim(
        expected_generation=0,
        owner_id="operation_a",
        consumer="start",
        claim_evidence_id="evidence_claim_a",
    )
    assert claimed.applied is True
    assert claimed.idempotent is False
    assert claimed.snapshot.state == "claimed"
    assert claimed.snapshot.generation == 1
    assert claimed.snapshot.claim_base_generation == 0

    activated = repository.activate(
        expected_generation=1,
        owner_id="operation_a",
        consumer="start",
        active_evidence_id="evidence_active_a",
    )
    assert activated.applied is True
    assert activated.snapshot.state == "active"
    assert activated.snapshot.generation == 2
    assert activated.snapshot.owner_id == "operation_a"
    assert activated.snapshot.consumer == "start"


def test_response_loss_retries_return_same_owner_without_advancing_generation(tmp_path: Path) -> None:
    repository = provision(tmp_path)
    first_claim = repository.claim(
        expected_generation=0,
        owner_id="operation_a",
        consumer="preview",
        claim_evidence_id="evidence_claim_a",
    )
    first_active = repository.activate(
        expected_generation=first_claim.snapshot.generation,
        owner_id="operation_a",
        consumer="preview",
        active_evidence_id="evidence_active_a",
    )

    repeated_claim = repository.claim(
        expected_generation=0,
        owner_id="operation_a",
        consumer="preview",
        claim_evidence_id="evidence_claim_a",
    )
    repeated_active = repository.activate(
        expected_generation=first_claim.snapshot.generation,
        owner_id="operation_a",
        consumer="preview",
        active_evidence_id="evidence_active_a",
    )

    assert repeated_claim.idempotent is True
    assert repeated_active.idempotent is True
    assert repeated_claim.snapshot == first_active.snapshot
    assert repeated_active.snapshot == first_active.snapshot
    assert repository.get_snapshot().generation == 2


def test_active_response_loss_retry_rejects_arbitrary_stale_generation(tmp_path: Path) -> None:
    repository = provision(tmp_path)
    claim = repository.claim(
        expected_generation=0,
        owner_id="operation_a",
        consumer="preview",
        claim_evidence_id="evidence_claim_a",
    )
    active = repository.activate(
        expected_generation=claim.snapshot.generation,
        owner_id="operation_a",
        consumer="preview",
        active_evidence_id="evidence_active_a",
    )

    stale = repository.activate(
        expected_generation=99,
        owner_id="operation_a",
        consumer="preview",
        active_evidence_id="evidence_active_a",
    )

    assert stale.applied is False
    assert stale.idempotent is False
    assert stale.reason == "coordinator_generation_mismatch"
    assert stale.snapshot == active.snapshot


def test_substituted_owner_consumer_generation_or_evidence_performs_zero_transition(tmp_path: Path) -> None:
    repository = provision(tmp_path)
    claimed = repository.claim(
        expected_generation=0,
        owner_id="operation_a",
        consumer="retry",
        claim_evidence_id="evidence_claim_a",
    )

    wrong_owner = repository.activate(
        expected_generation=claimed.snapshot.generation,
        owner_id="operation_b",
        consumer="retry",
        active_evidence_id="evidence_active_a",
    )
    wrong_consumer = repository.activate(
        expected_generation=claimed.snapshot.generation,
        owner_id="operation_a",
        consumer="delete",
        active_evidence_id="evidence_active_a",
    )
    wrong_generation = repository.activate(
        expected_generation=claimed.snapshot.generation + 1,
        owner_id="operation_a",
        consumer="retry",
        active_evidence_id="evidence_active_a",
    )
    substituted_claim = repository.claim(
        expected_generation=0,
        owner_id="operation_a",
        consumer="retry",
        claim_evidence_id="evidence_claim_substituted",
    )

    assert wrong_owner.reason == "coordinator_owner_mismatch"
    assert wrong_consumer.reason == "coordinator_owner_mismatch"
    assert wrong_generation.reason == "coordinator_generation_mismatch"
    assert substituted_claim.reason == "coordinator_not_idle"
    assert repository.get_snapshot() == claimed.snapshot


def test_only_one_concurrent_claim_wins_across_independent_connections(tmp_path: Path) -> None:
    path = Path(provision(tmp_path).db_path)
    start_barrier = threading.Barrier(2)

    def claim(index: int):
        repository = reopen(path)
        start_barrier.wait(timeout=10)
        return repository.claim(
            expected_generation=0,
            owner_id=f"operation_{index}",
            consumer="settings_save" if index == 0 else "local_supabase_start",
            claim_evidence_id=f"evidence_claim_{index}",
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(claim, range(2)))

    winners = [result for result in results if result.applied]
    losers = [result for result in results if not result.applied]
    assert len(winners) == 1
    assert len(losers) == 1
    assert losers[0].reason == "coordinator_not_idle"
    assert reopen(path).get_snapshot() == winners[0].snapshot


def test_only_one_concurrent_claim_wins_across_spawned_processes(tmp_path: Path) -> None:
    repository = provision(tmp_path)
    path = Path(repository.db_path)
    expected_file_binding_id = repository.expected_file_binding_id
    context = multiprocessing.get_context("spawn")
    start_barrier = context.Barrier(3)
    result_queue = context.Queue()
    processes = [
        context.Process(
            target=claim_in_process,
            args=(
                str(path),
                expected_file_binding_id,
                f"process_{index}",
                "settings_save" if index == 0 else "local_supabase_start",
                start_barrier,
                result_queue,
            ),
        )
        for index in range(2)
    ]
    try:
        for process in processes:
            process.start()
        start_barrier.wait(timeout=10)
        for process in processes:
            process.join(timeout=15)
        exitcodes = [process.exitcode for process in processes]
        results = [result_queue.get(timeout=5) for _ in processes]
    finally:
        for process in processes:
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
            process.close()
        result_queue.close()
        result_queue.join_thread()

    assert exitcodes == [0, 0]
    assert sum(applied for applied, _, _ in results) == 1
    assert sorted(reason for applied, reason, _ in results if not applied) == ["coordinator_not_idle"]


@pytest.mark.parametrize("consumer", sorted(COORDINATOR_CONSUMERS))
def test_every_canonical_consumer_can_be_bound_by_the_same_coordinator(
    tmp_path: Path,
    consumer: str,
) -> None:
    case_path = tmp_path / consumer
    case_path.mkdir()
    repository = provision(case_path)

    result = repository.claim(
        expected_generation=0,
        owner_id=f"operation_{consumer}",
        consumer=consumer,
        claim_evidence_id=f"evidence_{consumer}",
    )

    assert result.applied is True
    assert result.snapshot.consumer == consumer


def test_unknown_consumer_is_rejected_without_touching_the_store(tmp_path: Path) -> None:
    repository = provision(tmp_path)
    initial = repository.get_snapshot()

    with pytest.raises(ValueError, match="coordinator_consumer_invalid"):
        repository.claim(
            expected_generation=0,
            owner_id="operation_a",
            consumer="arbitrary_action",
            claim_evidence_id="evidence_claim_a",
        )

    assert repository.get_snapshot() == initial


@pytest.mark.parametrize("invalid_value", ["", "   ", "x" * 257, "owner\nforged", "owner/other"])
def test_claim_rejects_invalid_identifiers_without_touching_store(
    tmp_path: Path,
    invalid_value: str,
) -> None:
    repository = provision(tmp_path)
    initial = repository.get_snapshot()

    with pytest.raises(ValueError, match="owner_id_invalid"):
        repository.claim(
            expected_generation=0,
            owner_id=invalid_value,
            consumer="start",
            claim_evidence_id="evidence_claim_a",
        )

    assert repository.get_snapshot() == initial


def test_identifier_length_boundary_accepts_256_characters(tmp_path: Path) -> None:
    repository = provision(tmp_path)

    result = repository.claim(
        expected_generation=0,
        owner_id="o" * 256,
        consumer="start",
        claim_evidence_id="e" * 256,
    )

    assert result.applied is True
    assert result.snapshot.owner_id == "o" * 256


def test_transition_methods_reject_negative_generation_without_touching_store(tmp_path: Path) -> None:
    repository = provision(tmp_path)
    initial = repository.get_snapshot()

    with pytest.raises(ValueError, match="expected_generation_invalid"):
        repository.claim(
            expected_generation=-1,
            owner_id="operation_a",
            consumer="start",
            claim_evidence_id="evidence_claim_a",
        )
    assert repository.get_snapshot() == initial

    claim = repository.claim(
        expected_generation=0,
        owner_id="operation_a",
        consumer="start",
        claim_evidence_id="evidence_claim_a",
    )
    for method_name, evidence_parameter in (
        ("activate", "active_evidence_id"),
        ("mark_commit_unknown", "block_evidence_id"),
        ("mark_cleanup_blocked", "block_evidence_id"),
    ):
        with pytest.raises(ValueError, match="expected_generation_invalid"):
            getattr(repository, method_name)(
                expected_generation=-1,
                owner_id="operation_a",
                consumer="start",
                **{evidence_parameter: f"evidence_{method_name}"},
            )
        assert repository.get_snapshot() == claim.snapshot


@pytest.mark.parametrize("invalid_generation", [True, 1.5, "1", (1 << 63) - 1])
def test_transition_methods_reject_non_integer_or_overflow_generation(
    tmp_path: Path,
    invalid_generation: object,
) -> None:
    repository = provision(tmp_path)
    initial = repository.get_snapshot()

    with pytest.raises(ValueError, match="expected_generation_invalid"):
        repository.claim(
            expected_generation=invalid_generation,
            owner_id="operation_a",
            consumer="start",
            claim_evidence_id="evidence_claim_a",
        )

    assert repository.get_snapshot() == initial


def test_uncertain_external_floor_advance_leaves_repository_fail_closed(tmp_path: Path) -> None:
    repository = provision(tmp_path)

    def advance_then_lose_response(path: Path, expected: int, next_value: int) -> None:
        advance_test_generation_floor(path, expected, next_value)
        raise TimeoutError("floor store response lost")

    repository.advance_generation_floor = advance_then_lose_response

    with pytest.raises(
        OperationAuthorityUnavailableError,
        match="machine_authority_generation_floor_advance_failed",
    ):
        repository.claim(
            expected_generation=0,
            owner_id="operation_a",
            consumer="start",
            claim_evidence_id="evidence_claim_a",
        )

    with pytest.raises(
        OperationAuthorityBindingError,
        match="machine_authority_generation_floor_mismatch",
    ):
        repository.get_snapshot()


@pytest.mark.parametrize(
    ("method_name", "expected_state"),
    [
        ("mark_commit_unknown", "commit_unknown_blocked"),
        ("mark_cleanup_blocked", "cleanup_blocked"),
    ],
)
@pytest.mark.parametrize("starting_state", ["claimed", "active"])
def test_blocked_generations_are_idempotent_and_non_claimable(
    tmp_path: Path,
    method_name: str,
    expected_state: str,
    starting_state: str,
) -> None:
    repository = provision(tmp_path)
    claim = repository.claim(
        expected_generation=0,
        owner_id="operation_a",
        consumer="delete",
        claim_evidence_id="evidence_claim_a",
    )
    source = claim
    if starting_state == "active":
        source = repository.activate(
            expected_generation=claim.snapshot.generation,
            owner_id="operation_a",
            consumer="delete",
            active_evidence_id="evidence_active_a",
        )
    method = getattr(repository, method_name)
    blocked = method(
        expected_generation=source.snapshot.generation,
        owner_id="operation_a",
        consumer="delete",
        block_evidence_id="evidence_block_a",
    )
    repeated = method(
        expected_generation=source.snapshot.generation,
        owner_id="operation_a",
        consumer="delete",
        block_evidence_id="evidence_block_a",
    )
    takeover = repository.claim(
        expected_generation=blocked.snapshot.generation,
        owner_id="operation_b",
        consumer="preview",
        claim_evidence_id="evidence_claim_b",
    )

    assert blocked.applied is True
    assert blocked.snapshot.state == expected_state
    assert blocked.snapshot.generation == source.snapshot.generation + 1
    assert blocked.snapshot.block_evidence_id == "evidence_block_a"
    assert repeated.idempotent is True
    assert repeated.snapshot == blocked.snapshot
    assert takeover.applied is False
    assert takeover.reason == "coordinator_blocked"
    assert repository.get_snapshot() == blocked.snapshot

    stale = method(
        expected_generation=source.snapshot.generation + 99,
        owner_id="operation_a",
        consumer="delete",
        block_evidence_id="evidence_block_a",
    )
    assert stale.applied is False
    assert stale.idempotent is False
    assert stale.reason == "coordinator_generation_mismatch"
    assert stale.snapshot == blocked.snapshot

    blocked_claim_retry = repository.claim(
        expected_generation=0,
        owner_id="operation_a",
        consumer="delete",
        claim_evidence_id="evidence_claim_a",
    )
    blocked_activate_retry = repository.activate(
        expected_generation=claim.snapshot.generation,
        owner_id="operation_a",
        consumer="delete",
        active_evidence_id="evidence_active_a",
    )
    assert blocked_claim_retry.idempotent is False
    assert blocked_claim_retry.reason == "coordinator_blocked"
    assert blocked_activate_retry.idempotent is False
    assert blocked_activate_retry.reason == "coordinator_blocked"


def test_schema_tamper_is_rejected_on_reopen(tmp_path: Path) -> None:
    path = Path(provision(tmp_path).db_path)
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA ignore_check_constraints=ON")
        connection.execute("UPDATE authority_metadata SET schema_version = 999 WHERE singleton = 1")

    with pytest.raises(OperationAuthorityBindingError, match="machine_authority_schema_version_mismatch"):
        reopen(path)


def test_binding_validation_rejects_impossible_state_evidence_combination(tmp_path: Path) -> None:
    path = Path(provision(tmp_path).db_path)
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA ignore_check_constraints=ON")
        connection.execute(
            """
            UPDATE machine_global_operation_coordinator
            SET state = 'active', owner_id = 'operation_a', consumer = 'start',
                claim_base_generation = 0, claim_evidence_id = 'evidence_claim_a',
                active_evidence_id = NULL
            WHERE singleton = 1
            """
        )

    with pytest.raises(
        OperationAuthorityBindingError,
        match="machine_coordinator_evidence_state_invalid",
    ):
        reopen(path)


@pytest.mark.parametrize("invalid_value", [-1, 1.5, "not_integer"])
def test_binding_validation_rejects_non_integer_or_negative_base_generation(
    tmp_path: Path,
    invalid_value: object,
) -> None:
    repository = provision(tmp_path)
    path = Path(repository.db_path)
    repository.claim(
        expected_generation=0,
        owner_id="operation_a",
        consumer="start",
        claim_evidence_id="evidence_claim_a",
    )
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA ignore_check_constraints=ON")
        connection.execute(
            "UPDATE machine_global_operation_coordinator SET claim_base_generation = ? WHERE singleton = 1",
            (invalid_value,),
        )

    with pytest.raises(OperationAuthorityBindingError, match="claim_base_generation_invalid"):
        reopen(path)


@pytest.mark.parametrize(
    ("column", "value"),
    [("state", "unknown_state"), ("consumer", "unknown_consumer")],
)
def test_schema_constraints_are_derived_from_canonical_values(
    tmp_path: Path,
    column: str,
    value: str,
) -> None:
    path = Path(provision(tmp_path).db_path)

    with sqlite3.connect(path) as connection, pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            f"UPDATE machine_global_operation_coordinator SET {column} = ? WHERE singleton = 1",
            (value,),
        )


def test_repository_rejects_wal_mode_before_reading_authority_state(tmp_path: Path) -> None:
    path = Path(provision(tmp_path).db_path)
    with sqlite3.connect(path) as connection:
        observed_mode = str(connection.execute("PRAGMA journal_mode=WAL").fetchone()[0]).lower()
    assert observed_mode == "wal"

    with pytest.raises(OperationAuthorityBindingError, match="machine_authority_journal_mode_mismatch"):
        reopen(path)


def test_repository_rejects_linked_sqlite_sidecar(tmp_path: Path) -> None:
    repository = provision(tmp_path)
    path = Path(repository.db_path)
    target = tmp_path / "sidecar-target"
    target.write_bytes(b"not a sqlite journal")
    sidecar = Path(f"{path}-journal")
    try:
        sidecar.symlink_to(target)
    except OSError:
        pytest.skip("symlink creation unavailable")

    with pytest.raises(OperationAuthorityUnavailableError, match="machine_authority_path_has_link_component"):
        repository.get_snapshot()


def test_open_repository_rejects_authority_file_replacement(tmp_path: Path) -> None:
    original_dir = tmp_path / "original"
    replacement_dir = tmp_path / "replacement"
    original_dir.mkdir()
    replacement_dir.mkdir()
    repository = provision(original_dir)
    original_path = Path(repository.db_path)
    replacement_path = Path(provision(replacement_dir).db_path)
    backup_path = original_dir / "operation_authority.backup"
    original_path.replace(backup_path)
    replacement_path.replace(original_path)

    with pytest.raises(OperationAuthorityBindingError, match="machine_authority_file_binding_mismatch"):
        repository.get_snapshot()


def test_fresh_repository_rejects_rollback_copy_with_old_generation(tmp_path: Path) -> None:
    repository = provision(tmp_path)
    path = Path(repository.db_path)
    expected_file_binding_id = repository.expected_file_binding_id
    rollback_copy = tmp_path / "rollback-copy.db"
    shutil.copy2(path, rollback_copy)
    repository.claim(
        expected_generation=0,
        owner_id="operation_a",
        consumer="start",
        claim_evidence_id="evidence_claim_a",
    )
    path.unlink()
    rollback_copy.replace(path)

    with pytest.raises(OperationAuthorityBindingError, match="machine_authority_file_binding_mismatch"):
        reopen(path, expected_file_binding_id=expected_file_binding_id)


def test_repository_rejects_in_place_rollback_with_same_file_identity(tmp_path: Path) -> None:
    repository = provision(tmp_path)
    path = Path(repository.db_path)
    rollback_copy = tmp_path / "rollback-copy.db"
    shutil.copy2(path, rollback_copy)
    original_identity = observed_file_binding(path)
    repository.claim(
        expected_generation=0,
        owner_id="operation_a",
        consumer="start",
        claim_evidence_id="evidence_claim_a",
    )

    shutil.copyfile(rollback_copy, path)

    assert observed_file_binding(path) == original_identity
    with pytest.raises(
        OperationAuthorityBindingError,
        match="machine_authority_generation_floor_mismatch",
    ):
        repository.get_snapshot()
