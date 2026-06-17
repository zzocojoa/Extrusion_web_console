from __future__ import annotations

from hashlib import sha256
from typing import Any

from backend.app.core.settings import Settings


OPERATIONAL_PLC_SOURCE_CLASSES = {"network", "drive_letter", "mounted"}


def source_path_class(path: str) -> str:
    normalized = path.strip()
    if not normalized:
        return "missing"
    if normalized.startswith("\\\\") or normalized.startswith("//"):
        return "network"
    if len(normalized) >= 3 and normalized[1] == ":" and normalized[2] in {"\\", "/"}:
        return "drive_letter"
    if normalized.startswith("/mnt/"):
        return "mounted"
    return "local"


def source_path_fingerprint(path: str) -> str | None:
    normalized = path.strip()
    if not normalized:
        return None
    canonical = normalized.replace("\\", "/").lower()
    return sha256(canonical.encode("utf-8")).hexdigest()[:16]


def source_gate_snapshot(settings: Settings) -> dict[str, Any]:
    return {
        "plc": {
            "pathClass": source_path_class(settings.plc_data_dir),
            "pathFingerprint": source_path_fingerprint(settings.plc_data_dir),
        },
        "temperature": {
            "pathClass": source_path_class(settings.temperature_data_dir),
            "pathFingerprint": source_path_fingerprint(settings.temperature_data_dir),
        },
        "supabaseDbUrlConfigured": bool(settings.supabase_db_url),
    }
