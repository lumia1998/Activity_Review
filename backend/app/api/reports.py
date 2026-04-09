from fastapi import APIRouter, Query
from pydantic import BaseModel

from ..services.data_service import get_report
from ..services.report_service import export_report_markdown, generate_report_for_date

router = APIRouter()


class GenerateReportPayload(BaseModel):
    date: str
    force: bool = True
    locale: str | None = None


class ExportReportPayload(BaseModel):
    date: str
    content: str
    exportDir: str
    locale: str | None = None


@router.get("/{date}")
async def saved_report(date: str, locale: str | None = Query(default=None)) -> dict | None:
    return get_report(date, locale)


@router.post("/generate")
async def generate_report(payload: GenerateReportPayload) -> dict:
    return generate_report_for_date(payload.date, payload.force, payload.locale)


@router.post("/export-markdown")
async def export_markdown(payload: ExportReportPayload) -> str:
    return export_report_markdown(payload.date, payload.content, payload.exportDir, payload.locale)
