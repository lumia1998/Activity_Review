import json
from pathlib import Path
from typing import Any

from ..core.paths import config_path

DEFAULT_CONFIG: dict[str, Any] = {
    "theme": "system",
    "ai_mode": "local",
    "lightweight_mode": False,
    "hide_dock_icon": False,
    "work_start_hour": 9,
    "work_start_minute": 0,
    "work_end_hour": 18,
    "work_end_minute": 0,
    "background_opacity": 0.25,
    "background_blur": 1,
    "background_image": None,
    "app_category_rules": [],
    "domain_semantic_rules": [],
    "storage": {
        "screenshot_retention_days": 7,
        "metadata_retention_days": 30,
        "storage_limit_mb": 2048,
        "jpeg_quality": 85,
        "max_image_width": 1280,
        "screenshot_display_mode": "active_window",
    },
    "privacy": {
        "app_rules": [],
        "excluded_keywords": [],
        "excluded_domains": [],
        "filter_sensitive": True,
    },
    "text_model_profiles": [],
    "daily_report_custom_prompt": "",
    "daily_report_export_dir": None,
}


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _merge_dict(base: dict[str, Any], loaded: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in loaded.items():
        base_value = merged.get(key)
        if isinstance(base_value, dict) and isinstance(value, dict):
            merged[key] = _merge_dict(base_value, value)
        else:
            merged[key] = value
    return merged


def load_config() -> dict[str, Any]:
    path = config_path()
    if not path.exists():
        return json.loads(json.dumps(DEFAULT_CONFIG))

    with path.open("r", encoding="utf-8") as file:
        loaded = json.load(file)

    return _merge_dict(DEFAULT_CONFIG, loaded)


def save_config(config: dict[str, Any]) -> dict[str, Any]:
    path = config_path()
    ensure_parent(path)
    merged = _merge_dict(DEFAULT_CONFIG, config)
    with path.open("w", encoding="utf-8") as file:
        json.dump(merged, file, ensure_ascii=False, indent=2)
    return merged
