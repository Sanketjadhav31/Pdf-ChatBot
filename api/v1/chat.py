from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import ChatMessage as ChatMessageModel
from database import ChatSession as ChatSessionModel
from database import User, get_current_user, get_db
from models.schemas import (
    ChatHistoryItem,
    ChatHistoryResponse,
    ChatRequest,
    ChatResponse,
    ChatSessionSummary,
)
from services.rag_service import chat_orchestrator
from services.llm_service import llm_service


router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    """
    Chat endpoint that uses RAG with real LLM (Google or Ollama).
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
    
    # Persist chat session + messages
    session_id = result["session_id"]
    session: ChatSessionModel | None = (
        db.query(ChatSessionModel)
        .filter(
            ChatSessionModel.id == session_id,
            ChatSessionModel.user_id == current_user.id,
        )
        .first()
    )

    if session is None:
        # Create a new chat session
        title = request.question.strip()[:60] or "New chat"
        session = ChatSessionModel(
            id=session_id,
            user_id=current_user.id,
            title=title,
        )
        db.add(session)
        db.flush()

    # Store user question and assistant answer
    user_msg = ChatMessageModel(
        session_id=session.id,
        user_id=current_user.id,
        role="user",
        content=request.question,
    )
    assistant_msg = ChatMessageModel(
        session_id=session.id,
        user_id=current_user.id,
        role="assistant",
        content=answer,
    )
    db.add_all([user_msg, assistant_msg])
    db.commit()

    return ChatResponse(
        answer=answer,
        references=references,
        session_id=session_id,
    )


@router.get("/chat/sessions", response_model=List[ChatSessionSummary])
async def list_chat_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return chat sessions for the current user from the last 7 days.
    """
    cutoff = datetime.utcnow() - timedelta(days=7)
    sessions = (
        db.query(ChatSessionModel)
        .filter(
            ChatSessionModel.user_id == current_user.id,
            ChatSessionModel.created_at >= cutoff,
        )
        .order_by(ChatSessionModel.updated_at.desc())
        .all()
    )
    return [
        ChatSessionSummary(
            id=s.id,
            title=s.title,
            created_at=s.created_at,
            updated_at=s.updated_at,
        )
        for s in sessions
    ]


@router.get("/chat/sessions/{session_id}", response_model=ChatHistoryResponse)
async def get_chat_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = (
        db.query(ChatSessionModel)
        .filter(
            ChatSessionModel.id == session_id,
            ChatSessionModel.user_id == current_user.id,
        )
        .first()
    )
    if session is None:
        raise HTTPException(status_code=404, detail="Chat session not found")

    messages = (
        db.query(ChatMessageModel)
        .filter(
            ChatMessageModel.session_id == session.id,
            ChatMessageModel.user_id == current_user.id,
        )
        .order_by(ChatMessageModel.created_at.asc())
        .all()
    )

    return ChatHistoryResponse(
        session_id=session.id,
        title=session.title,
        messages=[
            ChatHistoryItem(
                id=m.id,
                role=m.role,
                content=m.content,
                created_at=m.created_at,
            )
            for m in messages
        ],
    )


@router.delete("/chat/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = (
        db.query(ChatSessionModel)
        .filter(
            ChatSessionModel.id == session_id,
            ChatSessionModel.user_id == current_user.id,
        )
        .first()
    )
    if session is None:
        raise HTTPException(status_code=404, detail="Chat session not found")

    db.delete(session)
    db.commit()
    return {"ok": True}

