"""系统状态和截图/OCR API"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from ..services.idle_service import (
    get_platform_support,
    get_system_state,
    is_screen_locked,
    is_user_idle,
)
from ..services.ocr_log_service import append_ocr_log
from ..services.ocr_service import filter_sensitive_text, is_ocr_available, perform_ocr
from ..services.permission_service import check_permissions as get_permission_status
from ..services.screenshot_service import capture_screenshot, get_screenshot_full, get_screenshot_thumbnail

router = APIRouter()


class ScreenshotPathPayload(BaseModel):
    screenshotPath: str | None = None


class OcrPayload(BaseModel):
    imagePath: str


@router.get('/system-state')
async def system_state() -> dict[str, Any]:
    state = get_system_state()
    state['permissions'] = get_permission_status()
    state['ocr'] = is_ocr_available()
    state['platformSupport'] = get_platform_support()
    return state


@router.get('/platform-support')
async def platform_support() -> dict[str, Any]:
    return get_platform_support()


@router.get('/is-screen-locked')
async def screen_locked() -> dict[str, bool]:
    return {'locked': is_screen_locked()}


@router.get('/is-idle')
async def check_idle() -> dict[str, Any]:
    return {'idle': is_user_idle()}


@router.post('/take-screenshot')
async def take_screenshot() -> dict[str, Any] | None:
    result = capture_screenshot()
    if result:
        return {
            'path': result['path'],
            'thumbnailPath': result['thumbnail_path'],
            'hash': result['hash'],
            'timestamp': result['timestamp'],
        }
    return None


@router.post('/screenshot-thumbnail')
async def screenshot_thumbnail(payload: ScreenshotPathPayload) -> dict[str, str | None]:
    data = get_screenshot_thumbnail(payload.screenshotPath)
    return {'data': data}


@router.post('/screenshot-full')
async def screenshot_full(payload: ScreenshotPathPayload) -> dict[str, str | None]:
    data = get_screenshot_full(payload.screenshotPath)
    return {'data': data}


@router.post('/run-ocr')
async def run_ocr(payload: OcrPayload) -> dict[str, str | None]:
    text = perform_ocr(payload.imagePath)
    filtered = filter_sensitive_text(text) if text else None
    append_ocr_log({
        'imagePath': payload.imagePath,
        'success': bool(filtered),
        'textPreview': (filtered or '')[:200],
    })
    return {'text': filtered}


@router.get('/ocr-available')
async def ocr_available() -> dict[str, Any]:
    return is_ocr_available()


@router.get('/check-permissions')
async def check_permissions() -> dict[str, Any]:
    return get_permission_status()


@router.get('/is-work-time')
async def is_work_time() -> dict[str, Any]:
    from datetime import datetime
    from ..services.config_service import load_config

    config = load_config()
    start_hour = int(config.get('work_start_hour') or 9)
    end_hour = int(config.get('work_end_hour') or 18)
    now_hour = datetime.now().hour

    return {
        'isWorkTime': start_hour <= now_hour < end_hour,
        'currentHour': now_hour,
        'workStartHour': start_hour,
        'workEndHour': end_hour,
    }
