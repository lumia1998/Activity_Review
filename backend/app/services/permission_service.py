from __future__ import annotations

import sys
from typing import Any

from .ocr_service import is_ocr_available


def check_permissions() -> dict[str, Any]:
    permissions = {
        'platform': sys.platform,
        'screenCapture': True,
        'accessibility': sys.platform == 'win32',
        'foregroundWindow': sys.platform == 'win32',
        'ocrAvailable': bool(is_ocr_available().get('available')),
    }
    permissions['allGranted'] = bool(
        permissions['screenCapture'] and permissions['foregroundWindow']
    )
    return permissions
