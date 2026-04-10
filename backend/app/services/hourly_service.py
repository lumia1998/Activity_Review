"""每小时摘要自动生成服务"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

from .config_service import load_config
from .data_service import get_connection, database_path, table_exists, get_timeline


def generate_hourly_summaries(date: str) -> list[dict[str, Any]]:
    """为指定日期生成每小时摘要

    按小时聚合活动记录，生成文本摘要。

    Args:
        date: 日期字符串 (YYYY-MM-DD)

    Returns:
        生成的摘要列表
    """
    timeline = get_timeline(date, limit=5000, offset=0)
    if not timeline:
        return []

    # 按小时分组
    hour_groups: dict[int, list[dict]] = defaultdict(list)
    for item in timeline:
        ts = int(item.get('timestamp') or 0)
        try:
            hour = datetime.fromtimestamp(ts).hour
        except (OSError, ValueError):
            continue
        hour_groups[hour].append(item)

    results = []
    for hour in range(24):
        activities = hour_groups.get(hour, [])
        if not activities:
            continue

        total_duration = sum(int(a.get('duration') or 0) for a in activities)
        app_durations: dict[str, int] = defaultdict(int)
        category_durations: dict[str, int] = defaultdict(int)
        titles: list[str] = []

        for act in activities:
            app_name = act.get('app_name') or '未知应用'
            app_durations[app_name] += int(act.get('duration') or 0)
            category = act.get('category') or 'other'
            category_durations[category] += int(act.get('duration') or 0)
            title = (act.get('window_title') or '').strip()
            if title and title not in titles[-3:]:  # 避免连续重复
                titles.append(title)

        # 主要应用
        sorted_apps = sorted(app_durations.items(), key=lambda x: -x[1])
        main_apps = [name for name, _ in sorted_apps[:4]]
        dominant_app = sorted_apps[0][0] if sorted_apps else '未知应用'
        dominant_category = max(category_durations.items(), key=lambda x: x[1])[0] if category_durations else 'other'

        # 生成摘要文本
        summary_parts: list[str] = []

        # 主应用描述
        if sorted_apps:
            top_app = sorted_apps[0]
            minutes = top_app[1] // 60
            summary_parts.append(f'主要使用 {top_app[0]}（{minutes}分钟）')

        # 活动描述
        if titles:
            unique_titles = list(dict.fromkeys(titles))[:3]
            for t in unique_titles:
                if len(t) > 40:
                    t = t[:40] + '…'
                summary_parts.append(f'活动：{t}')

        # 分类描述
        sorted_cats = sorted(category_durations.items(), key=lambda x: -x[1])
        if sorted_cats:
            cat_names = [c[0] for c in sorted_cats[:3]]
            summary_parts.append(f'分类：{", ".join(cat_names)}')

        summary = '；'.join(summary_parts) if summary_parts else '无活动记录'

        # 保存到数据库
        _save_hourly_summary(date, hour, summary, main_apps, len(activities), total_duration)

        results.append({
            'date': date,
            'hour': hour,
            'summary': summary,
            'main_apps': ','.join(main_apps),
            'activity_count': len(activities),
            'total_duration': total_duration,
        })

    return results


def _save_hourly_summary(
    date: str,
    hour: int,
    summary: str,
    main_apps: list[str],
    activity_count: int,
    total_duration: int,
) -> None:
    """保存或更新小时摘要到数据库"""
    db_path = database_path()
    if not db_path.exists():
        return

    with get_connection() as connection:
        if not table_exists(connection, 'hourly_summaries'):
            return

        connection.execute(
            """
            INSERT INTO hourly_summaries (date, hour, summary, main_apps, activity_count, total_duration)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(date, hour) DO UPDATE SET
                summary = excluded.summary,
                main_apps = excluded.main_apps,
                activity_count = excluded.activity_count,
                total_duration = excluded.total_duration
            """,
            (date, hour, summary, ','.join(main_apps), activity_count, total_duration),
        )
        connection.commit()


def auto_generate_today_hourly_summaries() -> list[dict[str, Any]]:
    """自动生成今天的小时摘要（用于定时任务）"""
    today = datetime.now().strftime('%Y-%m-%d')
    return generate_hourly_summaries(today)
