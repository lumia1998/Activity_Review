from __future__ import annotations

from .base import ActiveWindowInfo, get_platform_support, is_window_eligible
from .providers import get_foreground_window_info

__all__ = [
    'ActiveWindowInfo',
    'get_foreground_window_info',
    'get_platform_support',
    'is_window_eligible',
]
