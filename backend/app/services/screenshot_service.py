"""截图捕获服务 - 使用 mss 跨平台截图 + PIL 图像处理"""
from __future__ import annotations

import hashlib
import sys
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image

from .config_service import load_config
from .data_service import data_dir_path

THUMBNAIL_WIDTH = 400
FULL_WIDTH = 1200
DEFAULT_JPEG_QUALITY = 85
_DEFAULT_MAX_IMAGE_WIDTH = 1280

_mss_instance = None


def _get_mss():
    global _mss_instance
    if _mss_instance is None:
        import mss
        _mss_instance = mss.mss()
    return _mss_instance


def screenshot_dir() -> Path:
    path = data_dir_path() / 'screenshots'
    path.mkdir(parents=True, exist_ok=True)
    return path


def _date_screenshot_dir(date_str: str | None = None) -> Path:
    date_str = date_str or datetime.now().strftime('%Y-%m-%d')
    path = screenshot_dir() / date_str
    path.mkdir(parents=True, exist_ok=True)
    return path


def _storage_config() -> dict[str, Any]:
    config = load_config()
    return config.get('storage') or {}


def _jpeg_quality() -> int:
    return int(_storage_config().get('jpeg_quality') or DEFAULT_JPEG_QUALITY)


def _max_image_width() -> int:
    return int(_storage_config().get('max_image_width') or _DEFAULT_MAX_IMAGE_WIDTH)


def capture_screenshot(monitor_index: int | None = None) -> dict[str, Any] | None:
    """捕获屏幕截图，保存到 screenshots/{date}/{timestamp}.jpg

    Args:
        monitor_index: 显示器索引，None 表示主显示器

    Returns:
        dict 包含 path, thumbnail_path, hash 等信息，或 None 表示失败
    """
    if not _storage_config().get('screenshots_enabled', True):
        return None

    try:
        sct = _get_mss()
        monitors = sct.monitors
        if not monitors:
            return None

        idx = monitor_index if monitor_index is not None else 0
        if idx < 0 or idx >= len(monitors):
            idx = 0

        raw = sct.grab(monitors[idx])
        img = Image.frombytes('RGB', raw.size, raw.bgra, 'raw', 'BGRX')
    except Exception:
        return None

    max_w = _max_image_width()
    if img.width > max_w:
        ratio = max_w / img.width
        img = img.resize((max_w, int(img.height * ratio)), Image.LANCZOS)

    date_str = datetime.now().strftime('%Y-%m-%d')
    now_ts = int(datetime.now().timestamp())
    save_dir = _date_screenshot_dir(date_str)
    filename = f'{now_ts}.jpg'
    file_path = save_dir / filename
    quality = _jpeg_quality()

    img.save(str(file_path), 'JPEG', quality=quality)

    # 缩略图
    thumb_width = THUMBNAIL_WIDTH
    thumb_img = img.copy()
    if thumb_img.width > thumb_width:
        ratio = thumb_width / thumb_img.width
        thumb_img = thumb_img.resize((thumb_width, int(thumb_img.height * ratio)), Image.LANCZOS)

    thumb_filename = f'{now_ts}_thumb.jpg'
    thumb_path = save_dir / thumb_filename
    thumb_img.save(str(thumb_path), 'JPEG', quality=max(quality - 10, 60))

    img_hash = _image_hash(img)

    return {
        'path': str(file_path),
        'thumbnail_path': str(thumb_path),
        'hash': img_hash,
        'width': img.width,
        'height': img.height,
        'timestamp': now_ts,
        'date': date_str,
    }


def _image_hash(img: Image.Image, hash_size: int = 8) -> str:
    """计算感知哈希 (pHash) 用于空闲检测相似度比较"""
    resized = img.resize((hash_size + 1, hash_size), Image.LANCZOS).convert('L')
    pixels = list(resized.getdata())
    rows = [pixels[i * (hash_size + 1):(i + 1) * (hash_size + 1)] for i in range(hash_size)]
    diff_bits = []
    for row in rows:
        for col in range(hash_size):
            diff_bits.append('1' if row[col] < row[col + 1] else '0')
    return hex(int(''.join(diff_bits), 2))[2:]


def hash_distance(hash1: str, hash2: str) -> int:
    """计算两个感知哈希的汉明距离"""
    try:
        val1 = int(hash1, 16)
        val2 = int(hash2, 16)
        return bin(val1 ^ val2).count('1')
    except (ValueError, TypeError):
        return 64


def get_screenshot_thumbnail(screenshot_path: str | None) -> str | None:
    """获取截图缩略图的 base64 编码"""
    if not screenshot_path:
        return None

    path = Path(screenshot_path)
    # 先尝试缩略图路径
    if path.exists():
        thumb_path = path.parent / (path.stem + '_thumb' + path.suffix)
        target = thumb_path if thumb_path.exists() else path
    else:
        return None

    try:
        img = Image.open(str(target))
        if img.width > THUMBNAIL_WIDTH:
            ratio = THUMBNAIL_WIDTH / img.width
            img = img.resize((THUMBNAIL_WIDTH, int(img.height * ratio)), Image.LANCZOS)
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=75)
        import base64
        return base64.b64encode(buffer.getvalue()).decode('ascii')
    except Exception:
        return None


def get_screenshot_full(screenshot_path: str | None) -> str | None:
    """获取截图完整尺寸的 base64 编码"""
    if not screenshot_path:
        return None

    path = Path(screenshot_path)
    if not path.exists():
        return None

    try:
        img = Image.open(str(path))
        if img.width > FULL_WIDTH:
            ratio = FULL_WIDTH / img.width
            img = img.resize((FULL_WIDTH, int(img.height * ratio)), Image.LANCZOS)
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=80)
        import base64
        return base64.b64encode(buffer.getvalue()).decode('ascii')
    except Exception:
        return None


def is_idle_by_screenshot(current_hash: str, previous_hash: str | None, threshold: int = 8) -> bool:
    """通过截图哈希判断是否空闲（屏幕内容无变化）"""
    if not previous_hash:
        return False
    return hash_distance(current_hash, previous_hash) <= threshold
