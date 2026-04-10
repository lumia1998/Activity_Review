"""空闲检测和屏幕锁定检测服务"""
from __future__ import annotations

import ctypes
import ctypes.wintypes
import os
import shutil
import subprocess
import sys

from .providers.common import get_platform_support, linux_desktop_environment, linux_session_type

user32 = None
if sys.platform == 'win32':
    try:
        user32 = ctypes.windll.user32
    except Exception:
        pass

DEFAULT_IDLE_TIMEOUT = 180


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [
        ('cbSize', ctypes.wintypes.UINT),
        ('dwTime', ctypes.wintypes.DWORD),
    ]


def _run_command(command: list[str], timeout: int = 3) -> str:
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return ''
    if result.returncode != 0:
        return ''
    return (result.stdout or '').strip()


def get_idle_seconds() -> int:
    if sys.platform == 'win32':
        return _get_idle_seconds_windows()
    if sys.platform == 'darwin':
        return _get_idle_seconds_macos()
    if sys.platform.startswith('linux'):
        return _get_idle_seconds_linux()
    return 0


def _get_idle_seconds_windows() -> int:
    if user32 is None:
        return 0
    try:
        info = LASTINPUTINFO()
        info.cbSize = ctypes.sizeof(LASTINPUTINFO)
        if user32.GetLastInputInfo(ctypes.byref(info)):
            millis = ctypes.windll.kernel32.GetTickCount() - info.dwTime
            return max(0, millis // 1000)
    except Exception:
        pass
    return 0


def _get_idle_seconds_macos() -> int:
    output = _run_command(['ioreg', '-c', 'IOHIDSystem'])
    if not output:
        return 0
    for line in output.splitlines():
        if 'HIDIdleTime' not in line:
            continue
        raw = line.split('=', 1)[-1].strip()
        try:
            nanoseconds = int(raw)
        except ValueError:
            continue
        return max(0, nanoseconds // 1_000_000_000)
    return 0


def _get_idle_seconds_linux() -> int:
    if shutil.which('xprintidle'):
        output = _run_command(['xprintidle'])
        if output.isdigit():
            return int(output) // 1000

    if shutil.which('loginctl') and os.getenv('XDG_SESSION_ID'):
        output = _run_command(['loginctl', 'show-session', os.getenv('XDG_SESSION_ID', ''), '-p', 'IdleSinceHintUSec'])
        if '=' in output:
            raw = output.split('=', 1)[-1].strip()
            if raw.isdigit() and int(raw) > 0:
                try:
                    now_usec = int(_run_command(['python', '-c', 'import time; print(int(time.time()*1000000))']))
                    return max(0, (now_usec - int(raw)) // 1_000_000)
                except ValueError:
                    return 0
    return 0


def is_user_idle(timeout: int | None = None) -> bool:
    threshold = timeout if timeout is not None else DEFAULT_IDLE_TIMEOUT
    return get_idle_seconds() >= threshold


def is_screen_locked() -> bool:
    if sys.platform == 'win32':
        return _is_screen_locked_windows()
    if sys.platform == 'darwin':
        return _is_screen_locked_macos()
    if sys.platform.startswith('linux'):
        return _is_screen_locked_linux()
    return False


def _is_screen_locked_windows() -> bool:
    if user32 is None:
        return False
    try:
        hdesk = user32.OpenInputDesktop(0, False, 0x0001)
        if hdesk:
            user32.CloseDesktop(hdesk)
            return False
        return True
    except Exception:
        return False


def _is_screen_locked_macos() -> bool:
    output = _run_command([
        'python',
        '-c',
        'from Quartz import CGSessionCopyCurrentDictionary; import json; print(json.dumps(CGSessionCopyCurrentDictionary() or {}))',
    ])
    if not output:
        return False
    lowered = output.lower()
    return 'cgssessiononsessionloginwindowkey' in lowered and 'true' in lowered


def _is_screen_locked_linux() -> bool:
    if shutil.which('loginctl') and os.getenv('XDG_SESSION_ID'):
        output = _run_command(['loginctl', 'show-session', os.getenv('XDG_SESSION_ID', ''), '-p', 'LockedHint'])
        if output.endswith('=yes'):
            return True
        if output.endswith('=no'):
            return False
    return False


def get_system_state() -> dict[str, object]:
    idle_seconds = get_idle_seconds()
    locked = is_screen_locked()
    session_type = linux_session_type() if sys.platform.startswith('linux') else None
    desktop_environment = linux_desktop_environment() if sys.platform.startswith('linux') else None
    return {
        'idle_seconds': idle_seconds,
        'is_idle': idle_seconds >= DEFAULT_IDLE_TIMEOUT,
        'is_screen_locked': locked,
        'platform': sys.platform,
        'session_type': session_type,
        'desktop_environment': desktop_environment,
    }
