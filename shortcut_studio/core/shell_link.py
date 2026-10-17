from __future__ import annotations

import ctypes
import os
import shutil
from ctypes import wintypes
from pathlib import Path


_INVALID_FILENAME_CHARS = '<>:"/\\|?*'
_RESERVED_NAMES = {"CON", "PRN", "AUX", "NUL"} | {
    f"{prefix}{number}" for prefix in ("COM", "LPT") for number in range(1, 10)
}


def safe_shortcut_name(folder_name: str) -> str:
    """Sanitize a folder name to create a valid Windows shortcut filename."""
    translated = "".join(
        "_" if char in _INVALID_FILENAME_CHARS or ord(char) < 32 else char
        for char in folder_name
    )
    translated = translated.rstrip(" .") or "Shortcut"
    if translated.upper() in _RESERVED_NAMES:
        translated += "_"
    return translated


def shortcut_path(target_folder: Path, folder_name: str) -> Path:
    """Compute the destination .lnk file path for a given folder name."""
    return target_folder / f"{safe_shortcut_name(folder_name)}.lnk"


def install_launch_item(source: Path, destination: Path) -> None:
    """Create an executable shortcut or preserve an existing Windows shortcut."""
    if source.suffix.casefold() == ".lnk":
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        if not destination.exists():
            raise OSError("Windows shortcut could not be copied")
        return
    create_shortcut(source, destination)


def create_shortcut(executable: Path, destination: Path) -> None:
    """Create a native shortcut with the Unicode Windows Shell Link COM API."""
    if os.name != "nt":
        raise OSError("Shortcut creation is supported on Windows only")
    destination.parent.mkdir(parents=True, exist_ok=True)
    _create_shell_link(executable.resolve(), destination.resolve())
    if not destination.exists():
        raise OSError("Windows reported success, but the shortcut was not created")


class _GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", ctypes.c_ubyte * 8),
    ]


def _guid(value: str) -> _GUID:
    result = _GUID()
    status = ctypes.windll.ole32.CLSIDFromString(value, ctypes.byref(result))
    _check_hresult(status, "read Windows interface identifier")
    return result


def _method(interface: ctypes.c_void_p, index: int, *argument_types):
    table = ctypes.cast(
        interface, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))
    ).contents
    prototype = ctypes.WINFUNCTYPE(
        ctypes.c_long, ctypes.c_void_p, *argument_types
    )
    return prototype(table[index])


def _check_hresult(result: int, action: str) -> None:
    if result < 0:
        unsigned = ctypes.c_uint32(result).value
        raise OSError(f"Could not {action} (Windows error 0x{unsigned:08X})")


def _release(interface: ctypes.c_void_p) -> None:
    if interface:
        _method(interface, 2)(interface)


def _create_shell_link(executable: Path, destination: Path) -> None:
    ole32 = ctypes.windll.ole32
    ole32.CoInitializeEx.argtypes = [ctypes.c_void_p, wintypes.DWORD]
    ole32.CoInitializeEx.restype = ctypes.c_long
    ole32.CoCreateInstance.argtypes = [
        ctypes.POINTER(_GUID),
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(_GUID),
        ctypes.POINTER(ctypes.c_void_p),
    ]
    ole32.CoCreateInstance.restype = ctypes.c_long

    # CLSID_ShellLink and IID_IShellLinkW are Windows SDK constants.
    shell_link_class = _guid("{00021401-0000-0000-C000-000000000046}")
    shell_link_interface = _guid("{000214F9-0000-0000-C000-000000000046}")
    persist_file_interface = _guid("{0000010B-0000-0000-C000-000000000046}")

    initialized = ole32.CoInitializeEx(None, 0x2)  # COINIT_APARTMENTTHREADED
    # RPC_E_CHANGED_MODE means COM was already initialized in another mode; it
    # remains safe to use and must not be uninitialized by this function.
    should_uninitialize = initialized in (0, 1)
    if initialized < 0 and ctypes.c_uint32(initialized).value != 0x80010106:
        _check_hresult(initialized, "initialize Windows shortcuts")

    shell_link = ctypes.c_void_p()
    persist_file = ctypes.c_void_p()
    try:
        status = ole32.CoCreateInstance(
            ctypes.byref(shell_link_class),
            None,
            0x1,  # CLSCTX_INPROC_SERVER
            ctypes.byref(shell_link_interface),
            ctypes.byref(shell_link),
        )
        _check_hresult(status, "open the Windows shortcut service")

        _check_hresult(
            _method(shell_link, 20, wintypes.LPCWSTR)(shell_link, str(executable)),
            "set shortcut target",
        )
        _check_hresult(
            _method(shell_link, 9, wintypes.LPCWSTR)(
                shell_link, str(executable.parent)
            ),
            "set shortcut working folder",
        )
        _check_hresult(
            _method(shell_link, 17, wintypes.LPCWSTR, ctypes.c_int)(
                shell_link, str(executable), 0
            ),
            "set shortcut icon",
        )

        query_interface = _method(
            shell_link,
            0,
            ctypes.POINTER(_GUID),
            ctypes.POINTER(ctypes.c_void_p),
        )
        _check_hresult(
            query_interface(
                shell_link,
                ctypes.byref(persist_file_interface),
                ctypes.byref(persist_file),
            ),
            "prepare the shortcut file",
        )
        _check_hresult(
            _method(persist_file, 6, wintypes.LPCWSTR, wintypes.BOOL)(
                persist_file, str(destination), True
            ),
            "save the shortcut",
        )
    finally:
        _release(persist_file)
        _release(shell_link)
        if should_uninitialize:
            ole32.CoUninitialize()
