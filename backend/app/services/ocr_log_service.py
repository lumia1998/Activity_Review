from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .data_service import data_dir_path


LOG_DIR_NAME = 'ocr_logs'


def _log_dir() -> Path:
    path = data_dir_path() / LOG_DIR_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def append_ocr_log(entry: dict[str, Any]) -> str:
    date_str = datetime.now().strftime('%Y-%m-%d')
    path = _log_dir() / f'{date_str}.jsonl'
    payload = {
        'timestamp': int(datetime.now().timestamp()),
        **entry,
    }
    with path.open('a', encoding='utf-8') as f:
        f.write(json.dumps(payload, ensure_ascii=False) + '\n')
    return str(path)
