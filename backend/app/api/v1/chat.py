from fastapi import APIRouter

from ...models.schemas import ChatRequest, ChatResponse
from ...services.rag_service import chat_orchestrator


router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Basic chat endpoint that routes questions through the in-memory RAG service.
    """
    return chat_orchestrator.handle_chat(request)

