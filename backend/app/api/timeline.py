from fastapi import APIRouter, Query

from ..services.data_service import get_activity, get_hourly_summaries, get_timeline

router = APIRouter()


@router.get("")
async def timeline(date: str, limit: int = Query(default=20), offset: int = Query(default=0)) -> list[dict]:
    return get_timeline(date=date, limit=limit, offset=offset)


@router.get("/activity/{activity_id}")
async def activity(activity_id: int) -> dict | None:
    return get_activity(activity_id)


@router.get("/hourly-summaries")
async def hourly_summaries(date: str) -> list[dict]:
    return get_hourly_summaries(date)
