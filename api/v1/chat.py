from fastapi import APIRouter

from models.schemas import ChatRequest, ChatResponse
from services.rag_service import chat_orchestrator
from services.llm_service import llm_service


router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Chat endpoint that uses RAG with real LLM (Ollama or OpenAI).
    """
    result = chat_orchestrator.handle_chat(request)
    
    # If it's an error response (no context key), return as is
    if isinstance(result, ChatResponse):
        return result
    
    # Generate answer using LLM
    answer, is_relevant = await llm_service.generate_response(
        prompt=request.question,
        context=result["context"]
    )
    
    # Only include references if the answer is actually based on the documents
    references = result["references"] if is_relevant else []
    
    return ChatResponse(
        answer=answer,
        references=references,
        session_id=result["session_id"],
    )

