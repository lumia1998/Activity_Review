import base64
import shutil
import subprocess
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
import sqlite3
from urllib.parse import urlparse
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from ..core.paths import (
    CONFIG_FILENAME,
    DATABASE_FILENAME,
    default_data_dir,
    resolve_data_dir,
    save_data_dir_preference,
)
from .config_service import load_config, save_config

BACKGROUND_IMAGE_NAME = "background.jpg"
MANAGED_DATA_ENTRIES = {
    CONFIG_FILENAME,
    DATABASE_FILENAME,
    f"{DATABASE_FILENAME}-shm",
    f"{DATABASE_FILENAME}-wal",
    "screenshots",
    "ocr_logs",
    "background.jpg",
    "update_settings.json",
}


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(database_path())
    connection.row_factory = sqlite3.Row
    return connection


def database_path() -> Path:
    return resolve_data_dir() / DATABASE_FILENAME


def table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    row = connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def data_dir_path() -> Path:
    return resolve_data_dir()


def background_image_path() -> Path:
    return data_dir_path() / BACKGROUND_IMAGE_NAME


def _extract_domain(raw_url: str | None) -> str | None:
    if not raw_url:
        return None
    normalized = raw_url.strip()
    if not normalized:
        return None
    if '://' not in normalized:
        normalized = f'https://{normalized}'
    try:
        parsed = urlparse(normalized)
    except ValueError:
        return None
    host = (parsed.hostname or '').strip().lower()
    return host or None


def initialize_database() -> None:
    data_dir_path().mkdir(parents=True, exist_ok=True)
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_reports (
                date TEXT NOT NULL,
                locale TEXT NOT NULL DEFAULT 'zh-CN',
                content TEXT NOT NULL,
                ai_mode TEXT,
                model_name TEXT,
                created_at INTEGER NOT NULL,
                PRIMARY KEY (date, locale)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER NOT NULL,
                app_name TEXT NOT NULL,
                window_title TEXT NOT NULL DEFAULT '',
                screenshot_path TEXT,
                ocr_text TEXT,
                category TEXT NOT NULL DEFAULT 'other',
                duration INTEGER NOT NULL DEFAULT 20,
                browser_url TEXT,
                executable_path TEXT,
                semantic_category TEXT,
                semantic_confidence REAL
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_activities_timestamp
            ON activities(timestamp DESC)
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS hourly_summaries (
                date TEXT NOT NULL,
                hour INTEGER NOT NULL,
                summary TEXT,
                main_apps TEXT,
                activity_count INTEGER NOT NULL DEFAULT 0,
                total_duration INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (date, hour)
            )
            """
        )
        existing_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(daily_reports)").fetchall()
        }
        if 'locale' not in existing_columns:
            connection.execute("ALTER TABLE daily_reports ADD COLUMN locale TEXT NOT NULL DEFAULT 'zh-CN'")
            connection.execute("UPDATE daily_reports SET locale = 'zh-CN' WHERE locale IS NULL OR TRIM(locale) = ''")
        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_daily_reports_date_locale
            ON daily_reports(date, locale)
            """
        )
        connection.commit()

def _normalize_dir(path_str: str, create: bool = True) -> Path:
    path = Path((path_str or '').strip()).expanduser()
    if not str(path).strip():
        raise ValueError('目标目录不能为空')
    if create:
        path.mkdir(parents=True, exist_ok=True)
    try:
        return path.resolve()
    except OSError:
        return path


def _copy_entry(source: Path, target: Path) -> int:
    if not source.exists():
        return 0
    if source.is_dir():
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True, exist_ok=True)
        copied = 0
        for item in source.rglob('*'):
            if not item.exists():
                continue
            relative = item.relative_to(source)
            destination = target / relative
            if item.is_dir():
                destination.mkdir(parents=True, exist_ok=True)
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, destination)
            copied += 1
        return copied
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return 1


def _is_subpath(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _icon_seed(value: str) -> int:
    return sum(ord(char) for char in value) % 255


def _generate_placeholder_icon(app_name: str) -> str:
    seed = _icon_seed(app_name or 'app')
    background = (64 + seed // 2, 110 + seed // 3, 180 + seed // 5)
    image = Image.new('RGBA', (96, 96), background + (255,))
    draw = ImageDraw.Draw(image)
    letter = (app_name or '?').strip()[:1].upper() or '?'
    font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), letter, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    draw.text(
        ((96 - text_width) / 2, (96 - text_height) / 2 - 2),
        letter,
        fill=(255, 255, 255, 255),
        font=font,
    )
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode('ascii')


def _empty_overview_stats(date_from: str | None = None, date_to: str | None = None) -> dict[str, Any]:
    return {
        "date": date_from if date_from == date_to else None,
        "date_from": date_from,
        "date_to": date_to,
        "total_duration": 0,
        "screenshot_count": 0,
        "browser_duration": 0,
        "work_time_duration": 0,
        "app_usage": [],
        "category_usage": [],
        "url_usage": [],
        "domain_usage": [],
        "browser_usage": [],
        "browser_stats": [],
        "hourly_activity": [],
        "hourly_activity_distribution": [],
        "top_domains": [],
    }


def _build_overview_stats(date_from: str, date_to: str) -> dict[str, Any]:
    db_path = database_path()
    if not db_path.exists():
        return _empty_overview_stats(date_from, date_to)

    with get_connection() as connection:
        if not table_exists(connection, "activities"):
            return _empty_overview_stats(date_from, date_to)

        total_row = connection.execute(
            """
            SELECT
              COALESCE(SUM(duration), 0) AS total_duration,
              COUNT(*) AS screenshot_count,
              COALESCE(SUM(CASE WHEN browser_url IS NOT NULL AND TRIM(browser_url) != '' THEN duration ELSE 0 END), 0) AS browser_duration
            FROM activities
            WHERE date(timestamp, 'unixepoch', 'localtime') BETWEEN ? AND ?
            """,
            (date_from, date_to),
        ).fetchone()

        apps = connection.execute(
            """
            SELECT app_name, COALESCE(SUM(duration), 0) AS duration, COUNT(*) AS count,
                   MAX(executable_path) AS executable_path
            FROM activities
            WHERE date(timestamp, 'unixepoch', 'localtime') BETWEEN ? AND ?
            GROUP BY app_name
            ORDER BY duration DESC, app_name ASC
            LIMIT 20
            """,
            (date_from, date_to),
        ).fetchall()

        categories = connection.execute(
            """
            SELECT category, COALESCE(SUM(duration), 0) AS duration
            FROM activities
            WHERE date(timestamp, 'unixepoch', 'localtime') BETWEEN ? AND ?
            GROUP BY category
            ORDER BY duration DESC, category ASC
            """,
            (date_from, date_to),
        ).fetchall()

        browser_rows = connection.execute(
            """
            SELECT app_name AS browser_name, MAX(executable_path) AS executable_path,
                   COALESCE(SUM(duration), 0) AS duration, COUNT(*) AS count
            FROM activities
            WHERE date(timestamp, 'unixepoch', 'localtime') BETWEEN ? AND ?
              AND browser_url IS NOT NULL AND TRIM(browser_url) != ''
            GROUP BY app_name
            ORDER BY duration DESC, browser_name ASC
            """,
            (date_from, date_to),
        ).fetchall()

        browser_detail_rows = connection.execute(
            """
            SELECT app_name AS browser_name,
                   executable_path,
                   browser_url,
                   semantic_category,
                   COALESCE(SUM(duration), 0) AS duration,
                   COUNT(*) AS count
            FROM activities
            WHERE date(timestamp, 'unixepoch', 'localtime') BETWEEN ? AND ?
              AND browser_url IS NOT NULL AND TRIM(browser_url) != ''
            GROUP BY app_name, executable_path, browser_url, semantic_category
            ORDER BY browser_name ASC, duration DESC, browser_url ASC
            """,
            (date_from, date_to),
        ).fetchall()

        hourly_rows = connection.execute(
            """
            SELECT CAST(strftime('%H', datetime(timestamp, 'unixepoch', 'localtime')) AS INTEGER) AS hour,
                   COALESCE(SUM(duration), 0) AS duration,
                   COUNT(*) AS count
            FROM activities
            WHERE date(timestamp, 'unixepoch', 'localtime') BETWEEN ? AND ?
            GROUP BY hour
            ORDER BY hour ASC
            """,
            (date_from, date_to),
        ).fetchall()

        domain_rows = connection.execute(
            """
            SELECT browser_url, duration
            FROM activities
            WHERE date(timestamp, 'unixepoch', 'localtime') BETWEEN ? AND ?
              AND browser_url IS NOT NULL AND TRIM(browser_url) != ''
            """,
            (date_from, date_to),
        ).fetchall()

    domain_map: dict[str, int] = {}
    url_map: dict[str, int] = {}
    for row in domain_rows:
        browser_url = row["browser_url"]
        duration = int(row["duration"] or 0)
        if browser_url:
            url_map[browser_url] = url_map.get(browser_url, 0) + duration
        domain = _extract_domain(browser_url)
        if domain:
            domain_map[domain] = domain_map.get(domain, 0) + duration

    domain_usage = [
        {"domain": domain, "duration": duration}
        for domain, duration in sorted(domain_map.items(), key=lambda item: (-item[1], item[0]))
    ]
    url_usage = [
        {"url": url, "duration": duration}
        for url, duration in sorted(url_map.items(), key=lambda item: (-item[1], item[0]))[:20]
    ]

    browser_detail_map: dict[tuple[str, str | None], dict[str, Any]] = {}
    for row in browser_detail_rows:
        browser_name = row["browser_name"] or 'Unknown Browser'
        executable_path = row["executable_path"]
        browser_key = (browser_name, executable_path)
        browser_entry = browser_detail_map.setdefault(
            browser_key,
            {
                "browser_name": browser_name,
                "executable_path": executable_path,
                "duration": 0,
                "count": 0,
                "domains": [],
            },
        )

        duration = int(row["duration"] or 0)
        count = int(row["count"] or 0)
        browser_entry["duration"] += duration
        browser_entry["count"] += count

        browser_url = row["browser_url"] or ''
        domain = _extract_domain(browser_url)
        if not domain:
            continue

        existing_domain = next((item for item in browser_entry["domains"] if item["domain"] == domain), None)
        if existing_domain is None:
            existing_domain = {
                "domain": domain,
                "duration": 0,
                "count": 0,
                "semantic_category": (row["semantic_category"] or '').strip() or None,
                "urls": [],
            }
            browser_entry["domains"].append(existing_domain)

        existing_domain["duration"] += duration
        existing_domain["count"] += count
        if not existing_domain.get("semantic_category"):
            existing_domain["semantic_category"] = (row["semantic_category"] or '').strip() or None
        existing_domain["urls"].append(
            {
                "url": browser_url,
                "duration": duration,
                "count": count,
            }
        )

    browser_usage = []
    for row in browser_rows:
        browser_key = (row["browser_name"] or 'Unknown Browser', row["executable_path"])
        browser_entry = browser_detail_map.get(
            browser_key,
            {
                "browser_name": row["browser_name"] or 'Unknown Browser',
                "executable_path": row["executable_path"],
                "duration": int(row["duration"] or 0),
                "count": int(row["count"] or 0),
                "domains": [],
            },
        )
        browser_entry["domains"] = sorted(
            [
                {
                    **domain_item,
                    "urls": sorted(domain_item["urls"], key=lambda item: (-item["duration"], item["url"])),
                }
                for domain_item in browser_entry["domains"]
            ],
            key=lambda item: (-item["duration"], item["domain"]),
        )
        browser_usage.append(browser_entry)

    browser_stats = [
        {
            "browser_name": browser["browser_name"],
            "executable_path": browser["executable_path"],
            "duration": browser["duration"],
            "count": browser["count"],
            "domain_count": len(browser["domains"]),
            "url_count": sum(len(domain["urls"]) for domain in browser["domains"]),
            "top_domains": [
                {
                    "domain": domain["domain"],
                    "duration": domain["duration"],
                    "count": domain["count"],
                    "semantic_category": domain.get("semantic_category"),
                }
                for domain in browser["domains"][:5]
            ],
        }
        for browser in browser_usage
    ]

    hourly_activity = [
        {"hour": int(row["hour"] or 0), "duration": int(row["duration"] or 0), "count": int(row["count"] or 0)}
        for row in hourly_rows
    ]
    hourly_activity_distribution = [
        {"hour": hour, "duration": next((item["duration"] for item in hourly_activity if item["hour"] == hour), 0)}
        for hour in range(24)
    ]

    return {
        "date": date_from if date_from == date_to else None,
        "date_from": date_from,
        "date_to": date_to,
        "total_duration": int(total_row["total_duration"] or 0) if total_row else 0,
        "screenshot_count": int(total_row["screenshot_count"] or 0) if total_row else 0,
        "browser_duration": int(total_row["browser_duration"] or 0) if total_row else 0,
        "work_time_duration": int(total_row["total_duration"] or 0) if total_row else 0,
        "app_usage": [dict(row) for row in apps],
        "category_usage": [dict(row) for row in categories],
        "url_usage": url_usage,
        "domain_usage": domain_usage,
        "browser_usage": browser_usage,
        "browser_stats": browser_stats,
        "hourly_activity": hourly_activity,
        "hourly_activity_distribution": hourly_activity_distribution,
        "top_domains": domain_usage[:10],
    }


def get_today_stats() -> dict[str, Any]:
    today = datetime.now().strftime("%Y-%m-%d")
    return _build_overview_stats(today, today)


def get_overview_stats(mode: str = "today", date_from: str | None = None, date_to: str | None = None) -> dict[str, Any]:
    if mode == "today" or (not date_from and not date_to):
        today = datetime.now().strftime("%Y-%m-%d")
        return _build_overview_stats(today, today)

    normalized_from = date_from or date_to
    normalized_to = date_to or date_from
    if not normalized_from or not normalized_to:
        return _empty_overview_stats(normalized_from, normalized_to)
    if normalized_from > normalized_to:
        normalized_from, normalized_to = normalized_to, normalized_from
    return _build_overview_stats(normalized_from, normalized_to)


def _normalize_locale(locale: str | None) -> str:
    normalized = (locale or '').strip()
    return normalized or 'zh-CN'


def get_report(date: str, locale: str | None = None) -> dict[str, Any] | None:
    db_path = database_path()
    if not db_path.exists():
        return None

    normalized_locale = _normalize_locale(locale)

    with get_connection() as connection:
        if not table_exists(connection, "daily_reports"):
            return None

        row = connection.execute(
            """
            SELECT date, locale, content, ai_mode, model_name, created_at
            FROM daily_reports
            WHERE date = ? AND locale = ?
            LIMIT 1
            """,
            (date, normalized_locale),
        ).fetchone()
        if row:
            return dict(row)

        fallback = connection.execute(
            """
            SELECT date, locale, content, ai_mode, model_name, created_at
            FROM daily_reports
            WHERE date = ?
            ORDER BY CASE WHEN locale = 'zh-CN' THEN 0 ELSE 1 END, created_at DESC
            LIMIT 1
            """,
            (date,),
        ).fetchone()

        return dict(fallback) if fallback else None


def get_activity(activity_id: int) -> dict[str, Any] | None:
    db_path = database_path()
    if not db_path.exists():
        return None

    with get_connection() as connection:
        if not table_exists(connection, "activities"):
            return None

        row = connection.execute(
            """
            SELECT
              id,
              timestamp,
              app_name,
              window_title,
              screenshot_path,
              ocr_text,
              category,
              duration,
              browser_url,
              executable_path,
              semantic_category,
              semantic_confidence
            FROM activities
            WHERE id = ?
            LIMIT 1
            """,
            (activity_id,),
        ).fetchone()
        return dict(row) if row else None


def get_timeline(date: str, limit: int = 20, offset: int = 0) -> list[dict[str, Any]]:
    db_path = database_path()
    if not db_path.exists():
        return []

    with get_connection() as connection:
        if not table_exists(connection, "activities"):
            return []

        rows = connection.execute(
            """
            SELECT
              id,
              timestamp,
              app_name,
              window_title,
              screenshot_path,
              ocr_text,
              category,
              duration,
              browser_url,
              executable_path,
              semantic_category,
              semantic_confidence
            FROM activities
            WHERE date(timestamp, 'unixepoch', 'localtime') = ?
            ORDER BY timestamp DESC, id DESC
            LIMIT ? OFFSET ?
            """,
            (date, limit, offset),
        ).fetchall()

        return [dict(row) for row in rows]


def get_hourly_summaries(date: str) -> list[dict[str, Any]]:
    db_path = database_path()
    if not db_path.exists():
        return []

    with get_connection() as connection:
        if not table_exists(connection, "hourly_summaries"):
            return []

        rows = connection.execute(
            """
            SELECT hour, summary, main_apps, activity_count, total_duration
            FROM hourly_summaries
            WHERE date = ?
            ORDER BY hour ASC
            """,
            (date,),
        ).fetchall()

        return [dict(row) for row in rows]


def get_storage_stats() -> dict[str, Any]:
    screenshots_dir = data_dir_path() / "screenshots"
    total_files = 0
    total_size_bytes = 0

    if screenshots_dir.exists():
        for file_path in screenshots_dir.rglob('*'):
            if file_path.is_file():
                total_files += 1
                total_size_bytes += file_path.stat().st_size

    return {
        "total_files": total_files,
        "total_size_bytes": total_size_bytes,
        "total_size_mb": round(total_size_bytes / 1024 / 1024, 2),
        "storage_limit_mb": 2048,
        "retention_days": 7,
    }


def get_data_dir() -> str:
    return str(data_dir_path())


def get_default_data_dir() -> str:
    return str(default_data_dir())


def open_data_dir() -> bool:
    path = data_dir_path()
    if not path.exists():
        return False
    try:
        subprocess.Popen(['explorer', str(path)])
        return True
    except OSError:
        return False


def clear_old_activities() -> dict[str, Any]:
    base_dir = data_dir_path()
    screenshots_dir = base_dir / 'screenshots'
    today = datetime.now().strftime('%Y-%m-%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    kept_dates = [today, yesterday]
    deleted_screenshots = 0

    if screenshots_dir.exists():
        for entry in screenshots_dir.iterdir():
            if not entry.is_dir() or entry.name in kept_dates:
                continue
            deleted_screenshots += sum(1 for item in entry.rglob('*') if item.is_file())
            shutil.rmtree(entry, ignore_errors=True)

    return {
        'deleted_screenshots': deleted_screenshots,
        'kept_dates': kept_dates,
        'message': f'已清理 {deleted_screenshots} 张旧截图，保留今天和昨天的数据',
    }


def change_data_dir(target_dir: str) -> dict[str, Any]:
    current_dir = data_dir_path()
    requested_dir = _normalize_dir(target_dir)

    if requested_dir == current_dir:
        return {
            'dataDir': str(current_dir),
            'oldDataDir': str(current_dir),
            'copiedFiles': 0,
            'replacedExistingData': False,
            'message': '数据目录未变化',
        }

    if _is_subpath(requested_dir, current_dir) or _is_subpath(current_dir, requested_dir):
        raise ValueError('新旧数据目录不能互为父子目录，请选择独立目录')

    copied_files = 0
    replaced_existing_data = False
    for entry_name in MANAGED_DATA_ENTRIES:
        source = current_dir / entry_name
        target = requested_dir / entry_name
        if target.exists():
            replaced_existing_data = True
        copied_files += _copy_entry(source, target)

    current_config = load_config()
    save_data_dir_preference(requested_dir)
    save_config(current_config)

    return {
        'dataDir': str(requested_dir),
        'oldDataDir': str(current_dir),
        'copiedFiles': copied_files,
        'replacedExistingData': replaced_existing_data,
        'message': f'数据目录已更新，已迁移 {copied_files} 个文件',
    }


def cleanup_old_data_dir(target_dir: str) -> dict[str, Any]:
    cleanup_dir = _normalize_dir(target_dir, create=False)
    current_dir = data_dir_path()

    if cleanup_dir == current_dir:
        raise ValueError('不能清理当前正在使用的数据目录')
    if _is_subpath(cleanup_dir, current_dir) or _is_subpath(current_dir, cleanup_dir):
        raise ValueError('为避免误删，当前数据目录与待清理目录不能互为父子目录')

    removed_entries = 0
    preserved_entries: list[str] = []

    if not cleanup_dir.exists():
        return {
            'removedEntries': 0,
            'preservedEntries': [],
            'message': '旧目录不存在，无需清理',
        }

    for entry in cleanup_dir.iterdir():
        if entry.name in MANAGED_DATA_ENTRIES:
            if entry.is_dir():
                shutil.rmtree(entry, ignore_errors=True)
            else:
                entry.unlink(missing_ok=True)
            removed_entries += 1
        else:
            preserved_entries.append(entry.name)

    if not any(cleanup_dir.iterdir()):
        cleanup_dir.rmdir()

    return {
        'removedEntries': removed_entries,
        'preservedEntries': preserved_entries,
        'message': '已清理旧目录中的 Activity Review 数据',
    }




def _normalize_app_name(app_name: str | None) -> str:
    return (app_name or '').strip().lower()


def _normalize_domain(domain: str | None) -> str:
    normalized = (domain or '').strip().lower()
    if not normalized:
        return ''
    if '://' in normalized:
        return _extract_domain(normalized) or ''
    return normalized


def set_app_category_rule(app_name: str, category: str, sync_history: bool = True) -> int:
    normalized_app_name = _normalize_app_name(app_name)
    normalized_category = (category or '').strip() or 'other'
    if not normalized_app_name:
        raise ValueError('app name is required')

    config = load_config()
    rules = [rule for rule in config.get('app_category_rules', []) if _normalize_app_name(rule.get('app_name')) != normalized_app_name]
    rules.append({
        'app_name': app_name.strip(),
        'category': normalized_category,
    })
    config['app_category_rules'] = rules
    save_config(config)

    if not sync_history:
        return 0

    db_path = database_path()
    if not db_path.exists():
        return 0

    with get_connection() as connection:
        if not table_exists(connection, 'activities'):
            return 0
        cursor = connection.execute(
            """
            UPDATE activities
            SET category = ?
            WHERE LOWER(TRIM(app_name)) = ?
            """,
            (normalized_category, normalized_app_name),
        )
        connection.commit()
        return int(cursor.rowcount or 0)


def set_domain_semantic_rule(domain: str, semantic_category: str, sync_history: bool = True) -> int:
    normalized_domain = _normalize_domain(domain)
    normalized_category = (semantic_category or '').strip() or '未知活动'
    if not normalized_domain:
        raise ValueError('domain is required')

    config = load_config()
    rules = [rule for rule in config.get('domain_semantic_rules', []) if _normalize_domain(rule.get('domain')) != normalized_domain]
    rules.append({
        'domain': normalized_domain,
        'semantic_category': normalized_category,
    })
    config['domain_semantic_rules'] = rules
    save_config(config)

    if not sync_history:
        return 0

    db_path = database_path()
    if not db_path.exists():
        return 0

    updated_count = 0
    with get_connection() as connection:
        if not table_exists(connection, 'activities'):
            return 0
        rows = connection.execute(
            """
            SELECT id, browser_url
            FROM activities
            WHERE browser_url IS NOT NULL AND TRIM(browser_url) != ''
            """
        ).fetchall()
        matched_ids = [row['id'] for row in rows if _extract_domain(row['browser_url']) == normalized_domain]
        if matched_ids:
            placeholders = ','.join('?' for _ in matched_ids)
            params = [normalized_category, *matched_ids]
            cursor = connection.execute(
                f"UPDATE activities SET semantic_category = ? WHERE id IN ({placeholders})",
                params,
            )
            updated_count = int(cursor.rowcount or 0)
            connection.commit()
    return updated_count


def get_running_apps() -> list[dict[str, Any]]:
    return []


def get_recent_apps() -> list[dict[str, Any]]:
    db_path = database_path()
    if not db_path.exists():
        return []

    with get_connection() as connection:
        if not table_exists(connection, "activities"):
            return []

        rows = connection.execute(
            """
            SELECT app_name, MAX(executable_path) AS executable_path, MAX(timestamp) AS last_seen
            FROM activities
            GROUP BY app_name
            ORDER BY last_seen DESC, app_name ASC
            LIMIT 50
            """
        ).fetchall()
        return [dict(row) for row in rows]


def _windows_icon_cache_dir() -> Path:
    cache_dir = data_dir_path() / '.icon-cache'
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _windows_icon_cache_key(app_name: str, executable_path: str | None) -> str:
    raw = f"{app_name}::{(executable_path or '').strip().lower()}"
    return ''.join(char if char.isalnum() else '_' for char in raw)[:120] or 'icon'


def _extract_windows_icon(executable_path: str) -> str | None:
    candidate = Path(executable_path)
    if not candidate.exists() or not candidate.is_file():
        return None

    cache_file = _windows_icon_cache_dir() / f"{_windows_icon_cache_key(candidate.stem, executable_path)}.b64"
    if cache_file.exists():
        cached = cache_file.read_text(encoding='utf-8').strip()
        if cached:
            return cached

    output_png = _windows_icon_cache_dir() / f"{_windows_icon_cache_key(candidate.stem, executable_path)}.png"
    powershell_script = """
Add-Type -AssemblyName System.Drawing
$path = [System.IO.Path]::GetFullPath($args[0])
$png = [System.IO.Path]::GetFullPath($args[1])
if (-not [System.IO.File]::Exists($path)) { exit 2 }
$icon = [System.Drawing.Icon]::ExtractAssociatedIcon($path)
if ($null -eq $icon) { exit 3 }
$bitmap = $icon.ToBitmap()
$bitmap.Save($png, [System.Drawing.Imaging.ImageFormat]::Png)
$bitmap.Dispose()
$icon.Dispose()
""".strip()

    try:
        result = subprocess.run(
            ['powershell', '-NoProfile', '-Command', powershell_script, str(candidate), str(output_png)],
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None

    if result.returncode != 0 or not output_png.exists():
        return None

    base64_icon = base64.b64encode(output_png.read_bytes()).decode('ascii')
    cache_file.write_text(base64_icon, encoding='utf-8')
    return base64_icon


def get_app_icon(app_name: str, executable_path: str | None = None) -> str | None:
    if executable_path:
        extracted = _extract_windows_icon(executable_path)
        if extracted:
            return extracted
    return _generate_placeholder_icon(app_name or 'app')


def get_background_image() -> str | None:
    path = background_image_path()
    if not path.exists() or not path.is_file():
        return None
    return base64.b64encode(path.read_bytes()).decode("ascii")


def save_background_image(data: str) -> str:
    image_bytes = base64.b64decode(data)
    path = background_image_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(image_bytes)
    return path.name


def clear_background_image() -> bool:
    path = background_image_path()
    if path.exists():
        path.unlink()
    return True
