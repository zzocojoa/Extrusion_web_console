from __future__ import annotations

import ctypes
import os
from pathlib import Path


class _Guid(ctypes.Structure):
    _fields_ = (
        ("data1", ctypes.c_uint32),
        ("data2", ctypes.c_uint16),
        ("data3", ctypes.c_uint16),
        ("data4", ctypes.c_ubyte * 8),
    )


MACHINE_AUTHORITY_RELATIVE_PATH = Path("ExtrusionWebConsole") / "authority" / "operation_authority.db"
_FOLDERID_PROGRAM_DATA = _Guid(
    0x62AB5D82,
    0xFDC1,
    0x4DC3,
    (ctypes.c_ubyte * 8)(0xA9, 0xDD, 0x07, 0x0D, 0x1D, 0x49, 0x5D, 0x97),
)


class MachineAuthorityLocationError(RuntimeError):
    """Raised when the fixed machine-wide authority location cannot be resolved."""


def resolve_machine_authority_db_path(
    *,
    platform_name: str | None = None,
) -> Path:
    """Return the fixed Windows machine-wide authority path.

    The path intentionally has no EWC-specific override. Operational state DB,
    package, and per-user configuration changes must not create a second
    authority domain.
    """

    platform = os.name if platform_name is None else platform_name
    if platform != "nt":
        raise MachineAuthorityLocationError("machine_authority_requires_windows")

    program_data = _resolve_program_data_known_folder()
    if not program_data.is_absolute():
        raise MachineAuthorityLocationError("machine_authority_program_data_not_absolute")
    return program_data / MACHINE_AUTHORITY_RELATIVE_PATH


def _resolve_program_data_known_folder() -> Path:
    """Resolve FOLDERID_ProgramData without trusting process environment."""

    try:
        shell32 = ctypes.WinDLL("shell32", use_last_error=True)
        ole32 = ctypes.WinDLL("ole32", use_last_error=True)
    except (AttributeError, OSError) as exc:
        raise MachineAuthorityLocationError("machine_authority_known_folder_api_unavailable") from exc

    get_known_folder_path = shell32.SHGetKnownFolderPath
    get_known_folder_path.argtypes = (
        ctypes.POINTER(_Guid),
        ctypes.c_uint32,
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_wchar_p),
    )
    get_known_folder_path.restype = ctypes.c_long
    ole32.CoTaskMemFree.argtypes = (ctypes.c_void_p,)
    ole32.CoTaskMemFree.restype = None

    raw_path = ctypes.c_wchar_p()
    result = get_known_folder_path(ctypes.byref(_FOLDERID_PROGRAM_DATA), 0, None, ctypes.byref(raw_path))
    try:
        if result != 0:
            raise MachineAuthorityLocationError("machine_authority_program_data_lookup_failed")
        value = (raw_path.value or "").strip()
        if not value:
            raise MachineAuthorityLocationError("machine_authority_program_data_missing")
        return Path(value)
    finally:
        ole32.CoTaskMemFree(ctypes.cast(raw_path, ctypes.c_void_p))
