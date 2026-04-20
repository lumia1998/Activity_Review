from fastapi import APIRouter
from pydantic import BaseModel

from ..services.runtime_service import (
    capture_activity_tick,
    get_recording_state,
    pause_recording,
    resume_recording,
    set_dock_visibility,
)
from ..services.update_service import (
    check_github_update,
    download_and_install_github_update,
    quit_app_for_update,
    should_check_updates,
    update_last_check_time,
)
from ..services.autostart_service import (
    disable_autostart,
    enable_autostart,
    is_autostart_enabled,
)

router = APIRouter()


class ActivityTickPayload(BaseModel):
    appName: str | None = None
    windowTitle: str | None = None
    browserUrl: str | None = None
    executablePath: str | None = None
    duration: int | None = None
    category: str | None = None
    semanticCategory: str | None = None


class DockVisibilityPayload(BaseModel):
    visible: bool = True


class GithubUpdatePayload(BaseModel):
    currentVersion: str | None = None
    expectedVersion: str | None = None


@router.get('/recording-state')
async def recording_state() -> list[bool]:
    return get_recording_state()


@router.post('/pause-recording')
async def pause() -> list[bool]:
    return pause_recording()


@router.post('/resume-recording')
async def resume() -> list[bool]:
    return resume_recording()


@router.post('/activity-tick')
async def activity_tick(payload: ActivityTickPayload) -> dict | None:
    return capture_activity_tick(payload.model_dump())


@router.post('/set-dock-visibility')
async def set_dock(payload: DockVisibilityPayload) -> bool:
    return set_dock_visibility(payload.visible)


@router.post('/check-github-update')
async def check_update(payload: GithubUpdatePayload) -> dict:
    return check_github_update(payload.currentVersion or payload.expectedVersion or '0.0.0')


@router.post('/download-and-install-github-update')
async def download_update(payload: GithubUpdatePayload) -> dict:
    return download_and_install_github_update(payload.expectedVersion or payload.currentVersion or '0.0.0')


@router.post('/update-last-check-time')
async def update_check_time() -> dict:
    return update_last_check_time()


@router.post('/quit-app-for-update')
async def quit_for_update() -> bool:
    return quit_app_for_update()


@router.get('/should-check-updates')
async def should_check() -> bool:
    return should_check_updates()


@router.post('/enable-autostart')
async def enable_startup() -> bool:
    return enable_autostart()


@router.post('/disable-autostart')
async def disable_startup() -> bool:
    return disable_autostart()


@router.get('/is-autostart-enabled')
async def autostart_enabled() -> bool:
    return is_autostart_enabled()
