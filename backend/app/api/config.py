from fastapi import APIRouter, Query
from pydantic import BaseModel

from ..services.config_service import load_config, save_config
from ..services.data_service import (
    change_data_dir,
    cleanup_old_data_dir,
    clear_background_image,
    clear_old_activities,
    get_app_icon,
    get_background_image,
    get_data_dir,
    get_default_data_dir,
    get_recent_apps,
    get_running_apps,
    get_storage_stats,
    open_data_dir,
    save_background_image,
    set_app_category_rule,
    set_domain_semantic_rule,
)

router = APIRouter()


class ConfigPayload(BaseModel):
    config: dict


class BackgroundImagePayload(BaseModel):
    data: str


class ChangeDataDirPayload(BaseModel):
    targetDir: str


class AppCategoryRulePayload(BaseModel):
    appName: str
    category: str
    syncHistory: bool = True


class DomainSemanticRulePayload(BaseModel):
    domain: str
    semanticCategory: str
    syncHistory: bool = True


@router.get("")
async def get_config() -> dict:
    return load_config()


@router.put("")
async def put_config(payload: ConfigPayload) -> dict:
    return save_config(payload.config)


@router.get("/storage-stats")
async def storage_stats() -> dict:
    return get_storage_stats()


@router.get("/data-dir")
async def data_dir() -> str:
    return get_data_dir()


@router.get("/default-data-dir")
async def default_data_dir() -> str:
    return get_default_data_dir()


@router.get("/running-apps")
async def running_apps() -> list[dict]:
    return get_running_apps()


@router.get("/recent-apps")
async def recent_apps() -> list[dict]:
    return get_recent_apps()


@router.get("/app-icon")
async def app_icon(appName: str = Query(...), executablePath: str | None = Query(default=None)) -> str | None:
    return get_app_icon(appName, executablePath)


@router.post("/open-data-dir")
async def open_current_data_dir() -> bool:
    return open_data_dir()


@router.post("/clear-old-activities")
async def clear_old_activity_data() -> dict:
    return clear_old_activities()


@router.post("/change-data-dir")
async def change_current_data_dir(payload: ChangeDataDirPayload) -> dict:
    return change_data_dir(payload.targetDir)


@router.post("/cleanup-old-data-dir")
async def cleanup_previous_data_dir(payload: ChangeDataDirPayload) -> dict:
    return cleanup_old_data_dir(payload.targetDir)


@router.post('/app-category-rule')
async def update_app_category_rule(payload: AppCategoryRulePayload) -> int:
    return set_app_category_rule(payload.appName, payload.category, payload.syncHistory)


@router.post('/domain-semantic-rule')
async def update_domain_semantic_rule(payload: DomainSemanticRulePayload) -> int:
    return set_domain_semantic_rule(payload.domain, payload.semanticCategory, payload.syncHistory)


@router.get("/background-image")
async def background_image() -> str | None:
    return get_background_image()


@router.post("/background-image")
async def save_background(payload: BackgroundImagePayload) -> str:
    return save_background_image(payload.data)


@router.delete("/background-image")
async def delete_background_image() -> bool:
    return clear_background_image()
