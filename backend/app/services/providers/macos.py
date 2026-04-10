from __future__ import annotations

from ..base import ActiveWindowInfo, normalize_display_app_name
from .common import run_command


def get_foreground_window_info() -> ActiveWindowInfo | None:
    script = (
        'from AppKit import NSWorkspace; '
        'app = NSWorkspace.sharedWorkspace().frontmostApplication(); '
        'name = app.localizedName() if app else ""; '
        'bundle = app.bundleIdentifier() if app else ""; '
        'pid = app.processIdentifier() if app else 0; '
        'print(f"{name}\t{bundle}\t{pid}")'
    )
    output = run_command(['python', '-c', script])
    if not output:
        return None
    app_name, _, rest = output.partition('\t')
    executable_path, _, pid_raw = rest.partition('\t')
    app_name = normalize_display_app_name(app_name)
    pid = int(pid_raw) if pid_raw.isdigit() else None
    return ActiveWindowInfo(
        hwnd=0,
        pid=pid,
        app_name=app_name,
        window_title=app_name,
        executable_path=executable_path or None,
    )
