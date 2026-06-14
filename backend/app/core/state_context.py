from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from backend.app.core.settings import DEFAULT_REPO_ROOT, Settings


@dataclass(frozen=True)
class StateContext:
    context_class: str
    label: str
    storage_status: str
    source: str

    def to_api(self) -> dict[str, str]:
        return {
            "contextClass": self.context_class,
            "label": self.label,
            "storageStatus": self.storage_status,
            "source": self.source,
        }


_DEFAULT_STATE_DB_PATH = str(Settings.model_fields["state_db_path"].default)
_LABELS = {
    "operator_package": "Operator/package state",
    "development_default": "Development state",
    "qa_temporary": "QA temporary state",
    "configured": "Configured state",
    "unknown": "Unknown state",
    "inaccessible": "State inaccessible",
}


def build_state_context(settings: Settings) -> StateContext:
    raw_path = (settings.state_db_path or "").strip()
    source = _state_source(settings, raw_path)
    if not raw_path:
        return _context("unknown", "unknown", source)

    try:
        path = Path(raw_path).expanduser()
        resolved = path.resolve(strict=False)
    except (OSError, RuntimeError, ValueError):
        return _context("unknown", "unknown", source)

    storage_status = _storage_status(path)
    if storage_status == "inaccessible":
        return _context("inaccessible", storage_status, source)

    return _context(_context_class(resolved, source), storage_status, source)


def _state_source(settings: Settings, raw_path: str) -> str:
    if "EWC_STATE_DB_PATH" in os.environ:
        return "env"
    if raw_path and raw_path != _DEFAULT_STATE_DB_PATH:
        return "init"
    return "default"


def _storage_status(path: Path) -> str:
    try:
        if path.exists():
            return "present"
        if path.parent.is_dir():
            return "missing"
    except OSError:
        return "inaccessible"
    return "inaccessible"


def _context_class(path: Path, source: str) -> str:
    if _is_under(path, Path(tempfile.gettempdir())):
        return "qa_temporary"
    if _is_under(path, DEFAULT_REPO_ROOT):
        return "development_default"
    if source == "default" and path.name == "web_console_state.db":
        return "operator_package"
    if "ExtrusionWebConsole" in path.parts and path.name == "web_console_state.db":
        return "operator_package"
    return "configured"


def _is_under(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent.resolve(strict=False))
        return True
    except (OSError, RuntimeError, ValueError):
        return False


def _context(context_class: str, storage_status: str, source: str) -> StateContext:
    return StateContext(
        context_class=context_class,
        label=_LABELS.get(context_class, _LABELS["unknown"]),
        storage_status=storage_status,
        source=source if source in {"default", "env", "init"} else "unknown",
    )
