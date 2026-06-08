import subprocess

import pytest

from backend.app.services.command_runner import AllowedCommandRunner, CommandPolicyError, redact_command_output, required_supabase_containers


def runner(project_id: str = "Extrusion_web_console") -> AllowedCommandRunner:
    return AllowedCommandRunner(r"C:\Users\user\Documents\GitHub\Extrusion_web_console", project_id=project_id)


def test_command_policy_allows_read_only_commands() -> None:
    policy = runner()

    assert policy.validate(["docker", "version", "--format", "{{json .}}"]) == ("docker", "version", "--format", "{{json .}}")
    assert policy.validate(["docker", "ps", "-a", "--format", "{{json .}}"]) == ("docker", "ps", "-a", "--format", "{{json .}}")
    assert policy.validate(["wsl", "-l", "-v"]) == ("wsl", "-l", "-v")
    assert policy.validate(["supabase", "--version"]) == ("supabase", "--version")


def test_supabase_start_requires_container_precheck() -> None:
    policy = runner()

    with pytest.raises(CommandPolicyError, match="required_container_precheck_missing"):
        policy.validate(["supabase", "start"])

    assert policy.validate(["supabase", "start"], required_containers_verified=True) == ("supabase", "start")


@pytest.mark.parametrize(
    "command",
    [
        ["supabase", "init"],
        ["supabase", "db", "reset"],
        ["docker", "run", "postgres"],
        ["docker", "create", "postgres"],
        ["docker", "rm", "supabase_db_Extrusion_web_console"],
        ["docker", "volume", "rm", "anything"],
        ["docker", "prune"],
        ["docker", "compose", "up"],
        ["docker", "start", "grafana_local"],
        ["docker", "stop", "grafana_local"],
        ["powershell", "-Command", "Get-Process"],
    ],
)
def test_command_policy_rejects_destructive_or_arbitrary_commands(command: list[str]) -> None:
    with pytest.raises(CommandPolicyError):
        runner().validate(command)


def test_command_policy_derives_allowed_containers_from_project_id() -> None:
    policy = runner()

    assert required_supabase_containers("Extrusion_web_console")[0] == "supabase_db_Extrusion_web_console"
    assert policy.validate(["docker", "start", "supabase_db_Extrusion_web_console"]) == (
        "docker",
        "start",
        "supabase_db_Extrusion_web_console",
    )
    with pytest.raises(CommandPolicyError, match="container_not_allowed"):
        policy.validate(["docker", "start", "supabase_db_Extrusion_data"])


def test_command_policy_legacy_fallback_requires_explicit_project_id() -> None:
    policy = runner(project_id="Extrusion_data")

    assert policy.validate(["docker", "stop", "supabase_db_Extrusion_data"]) == (
        "docker",
        "stop",
        "supabase_db_Extrusion_data",
    )
    with pytest.raises(CommandPolicyError, match="container_not_allowed"):
        policy.validate(["docker", "stop", "supabase_db_Extrusion_web_console"])


@pytest.mark.parametrize("project_id", ["", "bad project", "../bad", "bad;name", "bad|name"])
def test_required_supabase_containers_rejects_unsafe_project_id(project_id: str) -> None:
    with pytest.raises(CommandPolicyError):
        required_supabase_containers(project_id)


def test_command_runner_uses_subprocess_without_shell(monkeypatch: pytest.MonkeyPatch) -> None:
    observed = {}

    def fake_run(*args, **kwargs):
        observed["args"] = args
        observed["kwargs"] = kwargs
        return subprocess.CompletedProcess(args=args[0], returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = runner().run(["supabase", "--version"])

    assert result.ok
    assert observed["kwargs"]["shell"] is False
    assert observed["kwargs"]["encoding"] == "utf-8"
    assert observed["kwargs"]["errors"] == "replace"


def test_command_output_redacts_supabase_keys_and_bearer_tokens() -> None:
    value = """
    Authorization: Bearer abc.def.ghi
    anon_key: local-anon-secret
    service_role: local-service-role-secret
    service_key=local-service-key-secret
    service-key: local-service-dash-secret
    SUPABASE_ANON_KEY=local-anon-env-secret
    SUPABASE_SERVICE_ROLE_KEY=local-service-env-secret
    """

    redacted = redact_command_output(value)

    assert "local-anon-secret" not in redacted
    assert "local-service-role-secret" not in redacted
    assert "local-service-key-secret" not in redacted
    assert "local-service-dash-secret" not in redacted
    assert "local-anon-env-secret" not in redacted
    assert "local-service-env-secret" not in redacted
    assert "Bearer [redacted]" in redacted
