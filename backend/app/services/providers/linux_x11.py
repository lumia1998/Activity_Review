from __future__ import annotations

from ..base import ActiveWindowInfo, normalize_display_app_name
from .common import run_command


def get_foreground_window_info() -> ActiveWindowInfo | None:
    window_id = run_command(['xdotool', 'getactivewindow'])
    if not window_id:
        return None

    title = run_command(['xdotool', 'getwindowname', window_id])
    wm_class = run_command(['xprop', '-id', window_id, 'WM_CLASS'])
    pid_output = run_command(['xdotool', 'getwindowpid', window_id])

    app_name = title
    if wm_class and ' = ' in wm_class:
        app_name = wm_class.split(' = ', 1)[-1].split(',')[-1].strip().strip('"') or title

    pid = int(pid_output) if pid_output.isdigit() else None
    app_name = normalize_display_app_name(app_name)
    return ActiveWindowInfo(
        hwnd=int(window_id) if window_id.isdigit() else 0,
        pid=pid,
        app_name=app_name,
        window_title=title or app_name,
        executable_path=None,
    )
