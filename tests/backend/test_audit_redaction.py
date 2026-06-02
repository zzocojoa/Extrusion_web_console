from backend.app.db.audit_repository import REDACTED, redact_audit_payload, sanitize_text


def test_redaction_masks_sensitive_keys_recursively() -> None:
    redacted = redact_audit_payload(
        {
            "password": "pw",
            "service_role": "role",
            "SUPABASE_ANON_KEY": "anon",
            "nested": [{"db_url": "postgres://user:pass@localhost/db"}, {"safe": "value"}],
        }
    )

    assert redacted["password"] == REDACTED
    assert redacted["service_role"] == REDACTED
    assert redacted["SUPABASE_ANON_KEY"] == REDACTED
    assert redacted["nested"][0]["db_url"] == REDACTED
    assert redacted["nested"][1]["safe"] == "value"


def test_redaction_masks_secret_like_values() -> None:
    text = (
        "Authorization: Bearer abc.def.ghi "
        "jwt eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.signature "
        "postgresql://postgres:postgres@127.0.0.1:25432/postgres"
    )

    sanitized = sanitize_text(text)

    assert sanitized is not None
    assert "Bearer [redacted]" in sanitized
    assert "eyJhbGci" not in sanitized
    assert "postgres:postgres" not in sanitized
    assert REDACTED in sanitized


def test_error_message_is_capped_after_redaction() -> None:
    sanitized = sanitize_text("x" * 700)

    assert sanitized is not None
    assert len(sanitized) == 503
