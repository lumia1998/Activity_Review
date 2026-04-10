from __future__ import annotations

import sys

from ..base import ActiveWindowInfo
from .common import get_platform_support, linux_session_type


def get_foreground_window_info() -> ActiveWindowInfo | None:
    if sys.platform == 'win32':
        from .windows import get_foreground_window_info as impl
        return impl()
    if sys.platform == 'darwin':
        from .macos import get_foreground_window_info as impl
        return impl()
    if sys.platform.startswith('linux'):
        if linux_session_type() == 'x11':
            from .linux_x11 import get_foreground_window_info as impl
            return impl()
        from .linux_wayland import get_foreground_window_info as impl
        return impl()
    return None


__all__ = [
    'ActiveWindowInfo',
    'get_foreground_window_info',
    'get_platform_support',
]
