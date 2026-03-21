from datetime import datetime, timedelta
from typing import List
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import ChatMessage as ChatMessageModel
from database import ChatSession as ChatSessionModel
from database import ChatSessionDocument
from database import UploadedDocument
from database import User, get_current_user, get_db
from models.schemas import (
    ChatHistoryItem,
    ChatHistoryResponse,
    ChatRequest,
    DocumentMetadata,
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
    # Resolve which PDFs belong to this session (DB is the source of truth).
    # This fixes the "reopened session loses PDF context" bug.
    session_id = request.session_id or str(uuid.uuid4())

    # Persist / update session-linked documents:
    # - If request provides non-empty document_ids, treat them as the active PDFs for this turn
    #   and link them to the session in the DB.
    # - If request provides none/empty, fall back to documents already linked to the session.
    request_document_ids = request.document_ids or []
    request_document_ids = [d for d in request_document_ids if d]  # drop falsy

    # Ensure we have a session row (needed for linking documents).
    session = (
        db.query(ChatSessionModel)
        .filter(
            ChatSessionModel.id == session_id,
            ChatSessionModel.user_id == current_user.id,
        )
        .first()
    )
    if session is None:
        title = request.question.strip()[:60] or "New chat"
        session = ChatSessionModel(
            id=session_id,
            user_id=current_user.id,
            title=title,
        )
        db.add(session)
        db.flush()
    else:
        if not session.title:
            session.title = request.question.strip()[:60] or "New chat"

    # Decide the "effective" document_ids for this request.
    effective_document_ids: List[str] = []
    if request_document_ids:
        # Validate ownership: only link docs that belong to this user.
        owned_docs = (
            db.query(UploadedDocument)
            .filter(
                UploadedDocument.user_id == current_user.id,
                UploadedDocument.id.in_(request_document_ids),
            )
            .all()
        )
        effective_document_ids = [d.id for d in owned_docs]

        # Upsert links for this session.
        if effective_document_ids:
            # Delete links not in the new set (keeps session consistent).
            db.query(ChatSessionDocument).filter(
                ChatSessionDocument.session_id == session_id
            ).filter(
                ~ChatSessionDocument.document_id.in_(effective_document_ids)
            ).delete(synchronize_session=False)

            # Add missing links.
            existing_links = (
                db.query(ChatSessionDocument.document_id)
                .filter(ChatSessionDocument.session_id == session_id)
                .all()
            )
            existing_set = {row[0] for row in existing_links}
            for doc_id in effective_document_ids:
                if doc_id in existing_set:
                    continue
                db.add(ChatSessionDocument(session_id=session_id, document_id=doc_id))
    else:
        # Use previously linked docs.
        existing_links = (
            db.query(ChatSessionDocument.document_id)
            .filter(ChatSessionDocument.session_id == session_id)
            .all()
        )
        effective_document_ids = [row[0] for row in existing_links]

    # Touch session so it bubbles to top in sidebar.
    session.updated_at = datetime.utcnow()

    refusal_message = (
        "I can only answer questions based on the uploaded PDF. "
        "This information is not in your document."
    )
    upload_needed_message = "Please upload a PDF to get started."

    # Load last 3 exchanges (up to 6 messages) for conversation continuity.
    # These are persisted in DB and should be included in the LLM prompt
    # even for casual messages.
    history_messages = (
        db.query(ChatMessageModel)
        .filter(
            ChatMessageModel.session_id == session_id,
            ChatMessageModel.user_id == current_user.id,
        )
        .order_by(ChatMessageModel.created_at.desc())
        .limit(6)
        .all()
    )
    history_messages = list(reversed(history_messages))

    # Refusal-poisoning prevention:
    # Filter out pure refusals so they don't become "established context" for follow-ups.
    # Note: we still store refusals in DB for UI continuity; we just exclude them from LLM history.
    filtered_history_messages = []
    for m in history_messages:
        if (m.role or "").strip().lower() == "assistant" and (m.content or "").strip() == refusal_message:
            continue
        filtered_history_messages.append(m)

    history = [{"role": m.role, "content": m.content} for m in filtered_history_messages]

    history_for_classifier = history[-4:] if history else None
    classification = await llm_service.classify_message(
        request.question, history=history_for_classifier
    )

    # Safety fallback for rare classifier slips:
    # If the user clearly references a numbered/document point, treat as PDF-related.
    if classification == "OUT_OF_SCOPE":
        import re
        q_lower = (request.question or "").lower()
        doc_ref = bool(
            re.search(r"\b(point|item|paragraph|section|page)\b", q_lower)
            or re.search(
                r"\b\d+(st|nd|rd|th)?\s*(point|item|paragraph|section|page)\b",
                q_lower,
            )
            or re.search(
                r"\b(point|item|paragraph|section|page)\s*\b\d+(st|nd|rd|th)?\b",
                q_lower,
            )
            or ("this document" in q_lower)
            or ("this pdf" in q_lower)
            or ("uploaded pdf" in q_lower)
            or ("the pdf" in q_lower)
        )
        if doc_ref:
            classification = "PDF_QUESTION"

    # Route based on classification result.
    if classification == "SOCIAL":
        answer = await llm_service.generate_social_response(
            user_message=request.question,
            username=current_user.username,
        )
        references = []
        is_relevant = False

    elif classification == "OUT_OF_SCOPE":
        # No LLM call needed.
        answer = refusal_message
        references = []
        is_relevant = False

    else:
        # PDF_QUESTION path: build PDF context + answer with strict PDF rules.
        search_query = request.question

        # Query rewriting for follow-ups ("the 4th point", "it", "previous item", ...)
        # so RAG retrieval doesn't depend on ambiguous references.
        import re
        q_lower = (request.question or "").lower()
        looks_like_reference = bool(
            re.search(r"\b(point|item|paragraph|section|page)\b", q_lower)
            or re.search(r"\b\d+(st|nd|rd|th)?\b", q_lower)
            or re.search(r"\b(it|that|this|these|those|previous|earlier|above|mentioned)\b", q_lower)
        )
        if history and looks_like_reference:
            search_query = await llm_service.rewrite_search_query(
                request.question, history=history
            )

        orchestrator_request = request.copy(
            update={
                "session_id": session_id,
                # IMPORTANT: if effective_document_ids is empty, this must be
                # treated as "no PDF context for this request" (strict PDF mode).
                "document_ids": effective_document_ids,
                "question": search_query,
            }
        )

        result = chat_orchestrator.handle_chat(orchestrator_request)
        pdf_context = result["context"]

        if not pdf_context.strip():
            answer = upload_needed_message
            references = []
            is_relevant = False
        else:
            answer, is_relevant = await llm_service.generate_response(
                prompt=request.question,
                context=pdf_context,
                username=current_user.username,
                history=history,
            )
            references = result["references"] if is_relevant else []
    
    # Persist chat session + messages
    # (session row already exists above and has been touched)

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

#  last 7 days chat
@router.get("/chat/sessions", response_model=List[ChatSessionSummary])
async def list_chat_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
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

    # Resolve session-linked documents so the frontend can restore "active PDF"
    # state when the user reopens a saved chat.
    linked_doc_ids = (
        db.query(ChatSessionDocument.document_id)
        .filter(ChatSessionDocument.session_id == session.id)
        .all()
    )
    linked_doc_id_list = [row[0] for row in linked_doc_ids]

    documents: List[DocumentMetadata] = []
    if linked_doc_id_list:
        docs = (
            db.query(UploadedDocument)
            .filter(
                UploadedDocument.user_id == current_user.id,
                UploadedDocument.id.in_(linked_doc_id_list),
            )
            .all()
        )
        documents = [
            DocumentMetadata(document_id=d.id, filename=d.filename) for d in docs
        ]

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
        documents=documents,
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

    # Remove session-document links first to keep the DB consistent.
    db.query(ChatSessionDocument).filter(ChatSessionDocument.session_id == session_id).delete(
        synchronize_session=False
    )
    db.delete(session)
    db.commit()
    return {"ok": True}

