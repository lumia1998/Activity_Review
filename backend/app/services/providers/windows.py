from __future__ import annotations

import ctypes
import ctypes.wintypes
from pathlib import Path

from ..base import ActiveWindowInfo, normalize_display_app_name

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
PROCESS_VM_READ = 0x0010
MAX_PATH = 260

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
psapi = ctypes.windll.psapi


def _get_window_text(hwnd: int) -> str:
    length = user32.GetWindowTextLengthW(hwnd)
    if length <= 0:
        return ''
    buffer = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buffer, length + 1)
    return buffer.value.strip()


def _get_process_path(pid: int) -> str | None:
    process = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION | PROCESS_VM_READ, False, pid)
    if not process:
        return None
    try:
        buffer = ctypes.create_unicode_buffer(MAX_PATH * 4)
        size = ctypes.wintypes.DWORD(len(buffer))
        query_image = getattr(kernel32, 'QueryFullProcessImageNameW', None)
        if query_image and query_image(process, 0, buffer, ctypes.byref(size)):
            value = buffer.value.strip()
            return value or None
        if psapi.GetModuleFileNameExW(process, None, buffer, len(buffer)):
            value = buffer.value.strip()
            return value or None
    finally:
        kernel32.CloseHandle(process)
    return None


def _get_process_name(executable_path: str | None, fallback_title: str) -> str:
    if executable_path:
        stem = Path(executable_path).stem.strip()
        if stem:
            return stem
    title = (fallback_title or '').strip()
    return title[:64] or 'Unknown App'


def get_foreground_window_info() -> ActiveWindowInfo | None:
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return None

    title = _get_window_text(hwnd)
    if not title:
        return None

    pid = ctypes.wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    process_id = int(pid.value or 0) or None
    executable_path = _get_process_path(process_id) if process_id else None
    app_name = normalize_display_app_name(_get_process_name(executable_path, title))

    return ActiveWindowInfo(
        hwnd=int(hwnd),
        pid=process_id,
        app_name=app_name,
        window_title=title,
        executable_path=executable_path,
    )
