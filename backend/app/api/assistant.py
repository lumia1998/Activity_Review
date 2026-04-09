from fastapi import APIRouter
from pydantic import BaseModel

from ..services.assistant_service import chat_work_assistant, test_model_connection

router = APIRouter()


class AssistantPayload(BaseModel):
    question: str
    history: list[dict] | None = None
    modelConfig: dict | None = None
    locale: str | None = None


class ModelTestPayload(BaseModel):
    modelConfig: dict | None = None


@router.post('/chat')
async def chat(payload: AssistantPayload) -> dict:
    return chat_work_assistant(payload.question, payload.history)


@router.post('/test-model')
async def test_model(payload: ModelTestPayload) -> dict:
    return test_model_connection(payload.modelConfig)
