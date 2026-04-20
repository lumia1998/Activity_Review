"""工作智能 API - 会话、意图、周报、TODO"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any

from ..services.data_service import get_timeline
from ..services.work_intelligence_service import (
    build_work_sessions,
    analyze_intents,
    generate_weekly_review,
    extract_todos,
)
from ..services.app_classifier_service import get_app_category_overview, reclassify_app_history

router = APIRouter()


class DateRangePayload(BaseModel):
    dateFrom: str | None = None
    dateTo: str | None = None


class DatePayload(BaseModel):
    date: str


class ReclassifyPayload(BaseModel):
    appName: str
    category: str


@router.post('/work-sessions')
async def work_sessions(payload: DateRangePayload) -> list[dict[str, Any]]:
    date_from = payload.dateFrom or payload.dateTo
    date_to = payload.dateTo or payload.dateFrom
    if not date_from or not date_to:
        return []
    activities = get_timeline(date_from, limit=5000, offset=0) if date_from == date_to else _get_range_activities(date_from, date_to)
    sessions = build_work_sessions(activities)
    return [s.to_dict() for s in sessions]


@router.post('/recognize-intents')
async def recognize_intents(payload: DateRangePayload) -> dict[str, Any]:
    date_from = payload.dateFrom or payload.dateTo
    date_to = payload.dateTo or payload.dateFrom
    if not date_from or not date_to:
        return {'sessions': [], 'summary': []}
    activities = get_timeline(date_from, limit=5000, offset=0) if date_from == date_to else _get_range_activities(date_from, date_to)
    return analyze_intents(activities)


@router.post('/weekly-review')
async def weekly_review(payload: DateRangePayload) -> dict[str, Any]:
    date_from = payload.dateFrom or payload.dateTo
    date_to = payload.dateTo or payload.dateFrom
    if not date_from or not date_to:
        return {'title': '', 'markdown': '', 'totalDuration': 0, 'activeDays': 0, 'sessionCount': 0}
    activities = _get_range_activities(date_from, date_to)
    return generate_weekly_review(activities, date_from, date_to)


@router.post('/extract-todos')
async def extract_todo_items(payload: DateRangePayload) -> dict[str, Any]:
    date_from = payload.dateFrom or payload.dateTo
    date_to = payload.dateTo or payload.dateFrom
    if not date_from or not date_to:
        return {'items': [], 'summary': '未指定日期范围'}
    activities = get_timeline(date_from, limit=5000, offset=0) if date_from == date_to else _get_range_activities(date_from, date_to)
    return extract_todos(activities)


@router.get('/app-category-overview')
async def app_categories() -> list[dict[str, Any]]:
    return get_app_category_overview()


@router.post('/reclassify-history')
async def reclassify(payload: ReclassifyPayload) -> dict[str, Any]:
    count = reclassify_app_history(payload.appName, payload.category)
    return {'updated': count, 'appName': payload.appName, 'category': payload.category}


def _get_range_activities(date_from: str, date_to: str) -> list[dict[str, Any]]:
    """获取日期范围内的所有活动（按天查询拼接）"""
    from datetime import datetime, timedelta
    start = datetime.strptime(date_from, '%Y-%m-%d')
    end = datetime.strptime(date_to, '%Y-%m-%d')
    all_activities: list[dict[str, Any]] = []
    current = start
    while current <= end:
        day_str = current.strftime('%Y-%m-%d')
        day_activities = get_timeline(day_str, limit=5000, offset=0)
        all_activities.extend(day_activities)
        current += timedelta(days=1)
    return all_activities
