from fastapi import APIRouter, Query

from ..services.data_service import get_overview_stats, get_today_stats

router = APIRouter()


@router.get("/today")
async def today_stats() -> dict:
    return get_today_stats()


@router.get("/overview")
async def overview_stats(
    mode: str = Query(default="today"),
    dateFrom: str | None = Query(default=None),
    dateTo: str | None = Query(default=None),
) -> dict:
    return get_overview_stats(mode=mode, date_from=dateFrom, date_to=dateTo)
