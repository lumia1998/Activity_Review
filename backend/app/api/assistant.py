from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any

from ..services.assistant_service import chat_work_assistant, search_memory, test_model_connection

router = APIRouter()


class AssistantPayload(BaseModel):
    question: str
    history: list[dict] | None = None
    modelConfig: dict | None = None
    locale: str | None = None


class ModelTestPayload(BaseModel):
    modelConfig: dict | None = None


class SearchMemoryPayload(BaseModel):
    query: str
    limit: int = 8


@router.post('/chat')
async def chat(payload: AssistantPayload) -> dict:
    return chat_work_assistant(payload.question, payload.history, payload.locale)


@router.post('/test-model')
async def test_model(payload: ModelTestPayload) -> dict:
    return test_model_connection(payload.modelConfig)


@router.post('/search-memory')
async def search_mem(payload: SearchMemoryPayload) -> list[dict[str, Any]]:
    return search_memory(payload.query, payload.limit)
