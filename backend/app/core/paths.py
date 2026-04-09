import json
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SOURCE_PROJECT_ROOT = PROJECT_ROOT

APP_NAME = "activity-review"
DATABASE_FILENAME = "workreview.db"
CONFIG_FILENAME = "config.json"
DATA_DIR_PREFERENCE_FILENAME = "data-location.json"


def _windows_appdata_dir() -> Path | None:
    appdata = os.getenv("APPDATA")
    if appdata:
        return Path(appdata)
    return None


def data_root_dir() -> Path:
    return _windows_appdata_dir() or (Path.home() / "AppData" / "Roaming")


def config_root_dir() -> Path:
    return _windows_appdata_dir() or (Path.home() / "AppData" / "Roaming")


def default_data_dir() -> Path:
    return data_root_dir() / APP_NAME


def data_dir_preference_path() -> Path:
    return config_root_dir() / APP_NAME / DATA_DIR_PREFERENCE_FILENAME


def load_data_dir_preference() -> Path | None:
    path = data_dir_preference_path()
    if not path.exists():
        return None

    try:
        content = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    data_dir = str(content.get("data_dir", "")).strip()
    if not data_dir:
        return None
    return Path(data_dir)


def save_data_dir_preference(path: Path) -> Path:
    preference_path = data_dir_preference_path()
    preference_path.parent.mkdir(parents=True, exist_ok=True)
    preference_path.write_text(
        json.dumps({"data_dir": str(path)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return preference_path


def ensure_data_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    try:
        return path.resolve()
    except OSError:
        return path


def resolve_data_dir() -> Path:
    default_dir = default_data_dir()
    preferred_dir = load_data_dir_preference() or default_dir

    try:
        return ensure_data_dir(preferred_dir)
    except OSError:
        if preferred_dir != default_dir:
            try:
                return ensure_data_dir(default_dir)
            except OSError:
                pass

        fallback_dir = PROJECT_ROOT / "data"
        fallback_dir.mkdir(parents=True, exist_ok=True)
        return fallback_dir


def database_path() -> Path:
    return resolve_data_dir() / DATABASE_FILENAME


def config_path() -> Path:
    return resolve_data_dir() / CONFIG_FILENAME
