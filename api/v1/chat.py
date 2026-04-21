from datetime import datetime, timedelta
from typing import List
import uuid
import re

from fastapi import APIRouter, Depends, HTTPException

from database import get_current_user, get_database
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
from services.redis_service import redis_service
from logger_config import setup_logger, PerformanceTimer, log_step

logger = setup_logger(__name__)
router = APIRouter(tags=["chat"])

_SOCIAL_PREFIX_RE = re.compile(
    r"^\s*(hi+|hello+|hey+|hii+|heyy+|heyyy+|good\s+morning|good\s+afternoon|good\s+evening)\b[\s,!.:-]*",
    re.IGNORECASE,
)


def _normalize_filename(value: str) -> str:
    """Normalize filename to lowercase alphanumeric for fuzzy matching"""
    value = (value or "").strip().lower()
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def _resolve_pdf_scope(
    question: str,
    available_docs: List[dict],
    requested_doc_ids: List[str],
    active_doc_ids: List[str],
) -> List[str]:
    """Determine which PDFs to use for retrieval based on explicit requests, filename mentions, or active docs"""
    if requested_doc_ids:
        return requested_doc_ids

    available_ids = [d["_id"] for d in available_docs]
    if not available_ids:
        return []

    q = (question or "").lower()
    # Normalize separators and tolerate spacing/typos like:
    # "summarizethis", "all the pdf", "lastt all pdf", etc.
    q_norm = re.sub(r"[^a-z0-9]+", " ", q).strip()

    multi_doc_patterns = [
        r"\bboth\s+(the\s+)?(pdfs?|docs?|documents?|files?)\b",
        r"\ball\s+(the\s+)?(pdfs?|docs?|documents?|files?)\b",
        r"\b(previous|prev|last|lastt|earlier)\s+(pdfs?|docs?|documents?|files?)\b",
        r"\b(all|both)\s+(previous|prev|last|lastt|earlier)\s+(pdfs?|docs?|documents?|files?)\b",
        r"\b(previous|prev|last|lastt|earlier)\s+(all|both)\s+(the\s+)?(pdfs?|docs?|documents?|files?)\b",
        r"\b(all|both)\s+(the\s+)?(previous|prev|last|lastt|earlier)\b.*\b(pdfs?|docs?|documents?|files?)\b",
        r"\b(previous|prev|last|lastt|earlier)\b.*\b(all|both)\b.*\b(pdfs?|docs?|documents?|files?)\b",
    ]
    if any(re.search(p, q_norm) for p in multi_doc_patterns):
        return available_ids

    matched: List[str] = []
    normalized_question = _normalize_filename(question)
    for doc in available_docs:
        filename = doc.get("filename", "")
        normalized_filename = _normalize_filename(filename)
        stem = _normalize_filename(filename.rsplit(".", 1)[0] if "." in filename else filename)
        if not normalized_filename:
            continue
        if (
            normalized_filename in normalized_question
            or (stem and stem in normalized_question)
            or (f" {normalized_filename} " in f" {normalized_question} ")
        ):
            matched.append(doc["_id"])
    if matched:
        # Keep order and uniqueness
        ordered_unique = list(dict.fromkeys(matched))
        return ordered_unique

    # Default scope: latest active PDF for this session.
    # This prevents follow-up prompts like "explain in points" from
    # unexpectedly mixing old session documents.
    if active_doc_ids:
        active_set = set(active_doc_ids)
        scoped_active = [doc_id for doc_id in available_ids if doc_id in active_set]
        if scoped_active:
            return scoped_active

    return available_ids


def _split_social_prefix(user_message: str) -> tuple[str, str]:
    """Extract leading greeting from mixed message, returns (social_prefix, remainder)"""
    message = (user_message or "").strip()
    match = _SOCIAL_PREFIX_RE.match(message)
    if not match:
        return "", message
    prefix = match.group(0).strip(" ,.!:-")
    remainder = message[match.end():].strip(" ,.!:-")
    return prefix, remainder


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db = Depends(get_database),
    current_user: dict = Depends(get_current_user),
) -> ChatResponse:
    """Main chat endpoint: classify message, perform RAG search, generate answer with LLM"""
    with PerformanceTimer(logger, f"Chat Request: {request.question[:50]}..."):
        # Resolve which PDFs belong to this session (DB is the source of truth).
        session_id = request.session_id or str(uuid.uuid4())

        log_step(logger, "Chat Request Received", {
            "User": current_user.get('username', 'Unknown'),
            "Session": session_id,
            "Question": request.question[:100] + "..." if len(request.question) > 100 else request.question,
            "Documents": len(request.document_ids or [])
        })

    # Persist / update session-linked documents
    request_document_ids = request.document_ids or []
    request_document_ids = [d for d in request_document_ids if d]

    # Ensure we have a session row (use upsert to avoid duplicate key errors)
    session = await db.chat_sessions.find_one({
        "_id": session_id,
        "user_id": current_user["_id"]
    })
    
    if session is None:
        title = request.question.strip()[:60] or "New chat"
        # Use update_one with upsert to avoid race conditions
        await db.chat_sessions.update_one(
            {"_id": session_id},
            {
                "$setOnInsert": {
                    "_id": session_id,
                    "user_id": current_user["_id"],
                    "title": title,
                    "created_at": datetime.utcnow() + timedelta(hours=5, minutes=30),
                    "active_document_ids": [],
                },
                "$set": {
                    "updated_at": datetime.utcnow() + timedelta(hours=5, minutes=30),
                }
            },
            upsert=True
        )
        # Fetch the session after upsert
        session = await db.chat_sessions.find_one({"_id": session_id})
    else:
        if not session.get("title"):
            await db.chat_sessions.update_one(
                {"_id": session_id},
                {"$set": {"title": request.question.strip()[:60] or "New chat"}}
            )

    # Decide the "effective" document_ids for this request
    effective_document_ids: List[str] = []
    # Store only explicitly attached docs for this user message payload.
    # This keeps UI chips accurate: follow-ups without upload won't show PDF cards.
    message_document_ids: List[str] = []
    if request_document_ids:
        # Validate ownership
        owned_docs = await db.uploaded_documents.find({
            "user_id": current_user["_id"],
            "_id": {"$in": request_document_ids}
        }).to_list(length=None)
        requested_owned_ids = [d["_id"] for d in owned_docs]
        message_document_ids = requested_owned_ids

        # Keep previously linked session docs and add newly requested docs.
        # This prevents losing older PDFs when a new PDF is attached later
        # in the same chat session.
        existing_links = await db.chat_session_documents.find({
            "session_id": session_id
        }).to_list(length=None)
        existing_set = {link["document_id"] for link in existing_links}

        for doc_id in requested_owned_ids:
            if doc_id not in existing_set:
                await db.chat_session_documents.insert_one({
                    "session_id": session_id,
                    "document_id": doc_id,
                    "created_at": datetime.utcnow() + timedelta(hours=5, minutes=30)
                })
                existing_set.add(doc_id)

        effective_document_ids = list(existing_set)
        # Track latest active docs for follow-up prompts without explicit filename.
        await db.chat_sessions.update_one(
            {"_id": session_id},
            {"$set": {"active_document_ids": requested_owned_ids}},
        )

    # Fallback to documents already linked to this session
    if not effective_document_ids:
        existing_links = await db.chat_session_documents.find({
            "session_id": session_id
        }).to_list(length=None)
        effective_document_ids = [link["document_id"] for link in existing_links]
    
    active_document_ids = session.get("active_document_ids", []) if session else []
    available_docs = []
    if effective_document_ids:
        available_docs = await db.uploaded_documents.find({
            "user_id": current_user["_id"],
            "_id": {"$in": effective_document_ids},
        }).to_list(length=None)
        
        if not active_document_ids:
            # Backfill active scope for old sessions to the most recent linked doc.
            latest_docs = sorted(
                available_docs,
                key=lambda d: d.get("created_at", datetime.min),
            )
            if latest_docs:
                active_document_ids = [latest_docs[-1]["_id"]]
                await db.chat_sessions.update_one(
                    {"_id": session_id},
                    {"$set": {"active_document_ids": active_document_ids}},
                )

    # Touch session
    await db.chat_sessions.update_one(
        {"_id": session_id},
        {"$set": {"updated_at": datetime.utcnow() + timedelta(hours=5, minutes=30)}}
    )
    first_name = llm_service._first_name_from_username(
    current_user.get("username", "User")
)
    refusal_message = (
    f"Hi {first_name}, I can only answer questions based on the uploaded PDF. "
    "This information is not in your document."
    )
    upload_needed_message = "Please upload a PDF to get started."

    # Try to load history from Redis cache first
    print(f"\n{'🔍'*40}")
    print(f"📦 REDIS CACHE CHECK")
    print(f"{'🔍'*40}")
    print(f"Session: {session_id}")
    print(f"User: {current_user.get('username', 'Unknown')}")
    
    logger.info(f"🔍 Checking Redis cache for session: {session_id}")
    history_from_cache = await redis_service.get_chat_history(
        user_id=current_user["_id"],
        session_id=session_id
    )
    
    if history_from_cache:
        # Cache hit - use cached history
        print(f"✅ REDIS CACHE HIT - Using {len(history_from_cache)} messages from Redis")
        print(f"⚡ Performance: ~1-5ms (Fast!)")
        print(f"{'='*80}\n")
        logger.info(f"✅ REDIS CACHE HIT - Using {len(history_from_cache)} messages from Redis cache")
        history_messages = history_from_cache
    else:
        # Cache miss - load from database
        print(f"❌ REDIS CACHE MISS - Loading from MongoDB")
        print(f"⏱️  Performance: ~50-100ms (Slower)")
        logger.info(f"💾 REDIS CACHE MISS - Loading history from MongoDB")
        history_messages = await db.chat_messages.find({
            "session_id": session_id,
            "user_id": current_user["_id"]
        }).sort("created_at", -1).limit(6).to_list(length=6)
        
        history_messages = list(reversed(history_messages))
        
        # Populate Redis cache with database history
        if history_messages:
            db_history = [
                {"role": m["role"], "content": m["content"]} 
                for m in history_messages
            ]
            await redis_service.set_chat_history(
                user_id=current_user["_id"],
                session_id=session_id,
                messages=db_history
            )
            print(f"✅ REDIS CACHE POPULATED - Stored {len(db_history)} messages for next time")
            logger.info(f"✅ REDIS CACHE POPULATED with {len(db_history)} messages from DB")
        print(f"{'='*80}\n")

    # Filter out pure refusals
    filtered_history_messages = []

    for m in history_messages:
        role = m.get("role", "").strip().lower()
        content = m.get("content", "").strip().lower()

        if (
            role == "assistant"
            and "only answer questions based on the uploaded pdf" in content
         ):
            continue

        filtered_history_messages.append(m)

    history = [{"role": m["role"], "content": m["content"]} for m in filtered_history_messages]

    print(f"\n{'#'*80}")
    print(f"💬 NEW CHAT REQUEST")
    print(f"{'#'*80}")
    print(f"User: {current_user.get('username', 'Unknown')}")
    print(f"Session: {session_id}")
    print(f"Question: {request.question}")
    print(f"Documents: {len(effective_document_ids)} linked")
    print(f"History: {len(history)} messages loaded")
    print(f"{'#'*80}\n")

    # OPTIMIZED: Single API call for classification + processing
    # This reduces API calls from 2-3 to 1-2 depending on message type
    classify_result = await llm_service.classify_and_process(
        request.question, 
        history=history,
        username=current_user["username"]
    )
    
    classification = classify_result["classification"]
    
    print(f"\n{'='*80}")
    print(f"📊 MESSAGE CLASSIFICATION")
    print(f"{'='*80}")
    print(f"Type: {classification}")
    print(f"{'='*80}\n")

    # Safety fallback for rare classifier slips
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

    # Route based on classification result
    if classification == "SOCIAL":
        # Use pre-generated response from classify_and_process (saves 1 API call)
        answer = classify_result.get("social_response") or await llm_service.generate_social_response(
            user_message=request.question,
            username=current_user["username"],
        )
        references = []
        is_relevant = False

    elif classification == "OUT_OF_SCOPE":
        social_prefix, remainder = _split_social_prefix(request.question)
        if social_prefix and remainder:
            greeting = await llm_service.generate_social_response(
                user_message=social_prefix,
                username=current_user["username"],
            )
            answer = f"{greeting} {refusal_message}"
        else:
            answer = refusal_message
        references = []
        is_relevant = False

    else:
        # PDF_QUESTION path
        # Use pre-generated rewritten query from classify_and_process (saves 1 API call)
        search_query = classify_result.get("rewritten_query") or request.question
        resolved_scope_ids = _resolve_pdf_scope(
            question=request.question,
            available_docs=available_docs,
            requested_doc_ids=message_document_ids,
            active_doc_ids=active_document_ids,
        )

        # Check if we have any valid documents to search
        if not resolved_scope_ids:
            answer = upload_needed_message
            references = []
            is_relevant = False
        else:
            orchestrator_request = request.copy(
                update={
                    "session_id": session_id,
                    "document_ids": resolved_scope_ids,
                    "question": search_query,
                }
            )

            rag_result = chat_orchestrator.handle_chat(orchestrator_request)
            pdf_context = rag_result["context"]

            if not pdf_context.strip():
                answer = upload_needed_message
                references = []
                is_relevant = False
            else:
                answer, is_relevant = await llm_service.generate_response(
                    prompt=request.question,
                    context=pdf_context,
                    username=current_user["username"],
                    history=history,
                )
                # Show references only for successful, document-grounded answers.
                # On rate-limit/API-failure/refusal paths, is_relevant is False.
                references = rag_result["references"] if is_relevant else []
    
    # Persist chat messages
    user_msg = {
        "_id": str(uuid.uuid4()),
        "session_id": session_id,
        "user_id": current_user["_id"],
        "role": "user",
        "content": request.question,
        "document_ids": message_document_ids,
        "created_at": datetime.utcnow() + timedelta(hours=5, minutes=30),
    }
    
    # Convert Reference objects to dicts for MongoDB
    references_dict = [
        {
            "document_id": ref.document_id,
            "page_number": ref.page_number,
            "document_heading": ref.document_heading,
            "paragraph_heading": ref.paragraph_heading,
            "snippet": ref.snippet if hasattr(ref, 'snippet') else None,
            "snippet_hover": ref.snippet_hover if hasattr(ref, 'snippet_hover') else None,
        }
        for ref in references
    ]
    
    assistant_msg = {
        "_id": str(uuid.uuid4()),
        "session_id": session_id,
        "user_id": current_user["_id"],
        "role": "assistant",
        "content": answer,
        "references": references_dict,
        "created_at": datetime.utcnow() + timedelta(hours=5, minutes=30),
    }
    await db.chat_messages.insert_many([user_msg, assistant_msg])

    # Update Redis cache with new messages
    print(f"\n{'💾'*40}")
    print(f"📝 REDIS CACHE UPDATE")
    print(f"{'💾'*40}")
    logger.info(f"💾 Updating Redis cache with new messages")
    
    redis_updated = await redis_service.add_message(
        user_id=current_user["_id"],
        session_id=session_id,
        role="user",
        content=request.question
    )
    redis_updated = await redis_service.add_message(
        user_id=current_user["_id"],
        session_id=session_id,
        role="assistant",
        content=answer
    ) and redis_updated
    
    if redis_updated:
        print(f"✅ REDIS CACHE UPDATED - Added 2 new messages")
        print(f"⚡ Next request will be faster (cache hit)")
    else:
        print(f"⚠️  REDIS UPDATE FAILED - Will use MongoDB next time")
    print(f"{'='*80}\n")

    print(f"\n{'='*80}")
    print(f"✅ CHAT RESPONSE COMPLETE")
    print(f"{'='*80}")
    print(f"Classification: {classification}")
    print(f"Answer length: {len(answer)} characters")
    print(f"References: {len(references)}")
    print(f"Messages saved to: MongoDB ✅ | Redis Cache {'✅' if redis_updated else '❌'}")
    print(f"{'#'*80}\n")

    return ChatResponse(
        answer=answer,
        references=references,
        session_id=session_id,
    )


@router.get("/chat/sessions", response_model=List[ChatSessionSummary])
async def list_chat_sessions(
    db = Depends(get_database),
    current_user: dict = Depends(get_current_user),
):
    """List user's chat sessions from last 7 days, sorted by most recent"""
    cutoff = datetime.utcnow() - timedelta(days=7) + timedelta(hours=5, minutes=30)
    sessions = await db.chat_sessions.find({
        "user_id": current_user["_id"],
        "created_at": {"$gte": cutoff}
    }).sort("updated_at", -1).to_list(length=None)
    
    return [
        ChatSessionSummary(
            id=s["_id"],
            title=s.get("title"),
            created_at=s["created_at"],
            updated_at=s["updated_at"],
        )
        for s in sessions
    ]


@router.get("/chat/sessions/{session_id}", response_model=ChatHistoryResponse)
async def get_chat_session(
    session_id: str,
    db = Depends(get_database),
    current_user: dict = Depends(get_current_user),
):
    """Get full chat history for a session with messages, references, and linked documents"""
    session = await db.chat_sessions.find_one({
        "_id": session_id,
        "user_id": current_user["_id"]
    })
    
    if session is None:
        raise HTTPException(status_code=404, detail="Chat session not found")

    messages = await db.chat_messages.find({
        "session_id": session_id,
        "user_id": current_user["_id"]
    }).sort("created_at", 1).to_list(length=None)

    # Resolve session-linked documents
    linked_docs = await db.chat_session_documents.find({
        "session_id": session_id
    }).to_list(length=None)
    linked_doc_ids = [link["document_id"] for link in linked_docs]

    documents: List[DocumentMetadata] = []
    if linked_doc_ids:
        docs = await db.uploaded_documents.find({
            "user_id": current_user["_id"],
            "_id": {"$in": linked_doc_ids}
        }).to_list(length=None)
        documents = [
            DocumentMetadata(document_id=d["_id"], filename=d["filename"]) 
            for d in docs
        ]

    # Build a lookup so each message can include attached document metadata.
    doc_lookup = {
        d.document_id: d
        for d in documents
    }

    return ChatHistoryResponse(
        session_id=session["_id"],
        title=session.get("title"),
        messages=[
            ChatHistoryItem(
                id=m["_id"],
                role=m["role"],
                content=m["content"],
                created_at=m["created_at"],
                attached_docs=[
                    doc_lookup[doc_id]
                    for doc_id in (m.get("document_ids") or [])
                    if doc_id in doc_lookup
                ],
                references=m.get("references", []),
            )
            for m in messages
        ],
        documents=documents,
    )


@router.delete("/chat/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,
    db = Depends(get_database),
    current_user: dict = Depends(get_current_user),
):
    """Delete chat session and all associated messages and document links"""
    session = await db.chat_sessions.find_one({
        "_id": session_id,
        "user_id": current_user["_id"]
    })
    
    if session is None:
        raise HTTPException(status_code=404, detail="Chat session not found")

    # Remove session-document links
    await db.chat_session_documents.delete_many({"session_id": session_id})
    
    # Delete messages
    await db.chat_messages.delete_many({"session_id": session_id})
    
    # Clear Redis cache for this session
    print(f"\n{'🗑️'*40}")
    print(f"🧹 REDIS CACHE CLEANUP")
    print(f"{'🗑️'*40}")
    print(f"Session: {session_id}")
    logger.info(f"🗑️ Clearing Redis cache for session: {session_id}")
    
    redis_cleared = await redis_service.clear_session(
        user_id=current_user["_id"],
        session_id=session_id
    )
    
    if redis_cleared:
        print(f"✅ REDIS CACHE CLEARED - Session removed from cache")
    else:
        print(f"⚠️  REDIS CLEAR FAILED - Cache may still contain session data")
    print(f"{'='*80}\n")
    
    # Delete session
    await db.chat_sessions.delete_one({"_id": session_id})
    
    return {"ok": True}
