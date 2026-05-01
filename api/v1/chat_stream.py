"""
Streaming chat endpoint for real-time LLM responses
"""
import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from database import get_current_user, get_database
from models.schemas import ChatRequest
from services.rag_service import chat_orchestrator
from services.llm_service import llm_service
from services.redis_service import redis_service
from logger_config import setup_logger

logger = setup_logger(__name__)
router = APIRouter(tags=["chat"])


async def stream_chat_response(
    request: ChatRequest,
    db,
    current_user: dict,
):
    """Stream chat response in real-time using Server-Sent Events (SSE)"""
    session_id = request.session_id or str(uuid.uuid4())
    
    try:
        # Send initial metadata
        yield f"data: {json.dumps({'type': 'metadata', 'session_id': session_id, 'provider': 'Ollama' if llm_service.use_ollama else 'Gemini', 'model': llm_service.model_name})}\n\n"
        
        # Load history from Redis or MongoDB
        history_from_cache = await redis_service.get_chat_history(
            user_id=str(current_user["_id"]),
            session_id=session_id
        )
        
        if history_from_cache:
            history_messages = history_from_cache
            yield f"data: {json.dumps({'type': 'status', 'message': '✅ Loaded history from cache'})}\n\n"
        else:
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
                    user_id=str(current_user["_id"]),
                    session_id=session_id,
                    messages=db_history
                )
                yield f"data: {json.dumps({'type': 'status', 'message': '✅ Cache populated from DB'})}\n\n"
    
        history = [{"role": m["role"], "content": m["content"]} for m in history_messages]
        
        # Classify message
        yield f"data: {json.dumps({'type': 'status', 'message': '🔍 Analyzing your question...'})}\n\n"
        
        classify_result = await llm_service.classify_and_process(
            request.question,
            history=history,
            username=current_user["username"]
        )
        
        classification = classify_result["classification"]
        yield f"data: {json.dumps({'type': 'classification', 'value': classification})}\n\n"
        
        # Handle different message types
        full_answer = ""
        references_dict = []
        
        if classification == "SOCIAL":
            answer = classify_result.get("social_response") or await llm_service.generate_social_response(
                user_message=request.question,
                username=current_user["username"],
            )
            full_answer = answer
            yield f"data: {json.dumps({'type': 'content', 'text': answer})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'answer': answer, 'references': []})}\n\n"
            
        elif classification == "OUT_OF_SCOPE":
            refusal_message = (
                f"Hi {llm_service._first_name_from_username(current_user.get('username', 'User'))}, "
                "I can only answer questions based on the uploaded PDF. "
                "This information is not in your document."
            )
            full_answer = refusal_message
            yield f"data: {json.dumps({'type': 'content', 'text': refusal_message})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'answer': refusal_message, 'references': []})}\n\n"
            
        else:
            # PDF_QUESTION path
            yield f"data: {json.dumps({'type': 'status', 'message': '📚 Searching document...'})}\n\n"
            
            search_query = classify_result.get("rewritten_query") or request.question
            
            # Get RAG context
            orchestrator_request = request.copy(update={"question": search_query})
            rag_result = chat_orchestrator.handle_chat(orchestrator_request)
            pdf_context = rag_result["context"]
            references = rag_result["references"]
            
            if not pdf_context.strip():
                upload_needed = "Please upload a PDF to get started."
                full_answer = upload_needed
                yield f"data: {json.dumps({'type': 'content', 'text': upload_needed})}\n\n"
                yield f"data: {json.dumps({'type': 'done', 'answer': upload_needed, 'references': []})}\n\n"
            else:
                # Send references first
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
                yield f"data: {json.dumps({'type': 'references', 'data': references_dict})}\n\n"
                
                # Stream the answer
                yield f"data: {json.dumps({'type': 'status', 'message': '🤖 Generating answer...'})}\n\n"
                
                thinking_text = ""
                is_in_thinking = False
                
                async for chunk in llm_service.generate_response_stream(
                    prompt=request.question,
                    context=pdf_context,
                    username=current_user["username"],
                    history=history,
                ):
                    # Check for special markers
                    if chunk.startswith("<<<STATUS>>>"):
                        # Extract status message and send it
                        status_msg = chunk.replace("<<<STATUS>>>", "").strip()
                        logger.info(f"📍 STATUS marker received: {status_msg}")
                        yield f"data: {json.dumps({'type': 'status', 'message': status_msg})}\n\n"
                        continue
                    elif chunk == "<<<THINKING_START>>>":
                        is_in_thinking = True
                        logger.info("📍 THINKING_START marker received")
                        continue
                    elif chunk == "<<<THINKING_END>>>":
                        is_in_thinking = False
                        logger.info("📍 THINKING_END marker received")
                        # Send any remaining thinking text
                        if thinking_text.strip():
                            yield f"data: {json.dumps({'type': 'thinking', 'text': thinking_text.strip()})}\n\n"
                        thinking_text = ""
                        continue
                    elif chunk == "<<<ANSWER_START>>>":
                        is_in_thinking = False
                        logger.info("📍 ANSWER_START marker received")
                        continue
                    
                    # Accumulate text based on section
                    if is_in_thinking:
                        thinking_text += chunk
                        # Stream thinking in real-time (every 15 chars for smooth typing effect)
                        if len(thinking_text) > 15 or chunk.endswith(('.', '!', '?', '\n')):
                            # Clean any remaining markers before sending
                            clean_thinking = thinking_text
                            for marker in ["[THINKING]", "[/THINKING]", "[ANSWER]", "[/ANSWER]"]:
                                clean_thinking = clean_thinking.replace(marker, "")
                            if clean_thinking.strip():
                                logger.info(f"📤 Sending thinking chunk: {clean_thinking[:50]}...")
                                yield f"data: {json.dumps({'type': 'thinking', 'text': clean_thinking.strip()})}\n\n"
                            thinking_text = ""
                    else:
                        full_answer += chunk
                        logger.info(f"📤 Sending answer chunk: {chunk[:20]}...")
                        yield f"data: {json.dumps({'type': 'content', 'text': chunk})}\n\n"
                    
                    # Force immediate flush - no sleep needed
                
                yield f"data: {json.dumps({'type': 'done', 'answer': full_answer, 'references': references_dict})}\n\n"
        
        # Save messages to database after streaming completes (for ALL message types)
        logger.info(f"💾 Saving chat to database - Session: {session_id}")
        
        user_msg = {
            "session_id": session_id,
            "user_id": current_user["_id"],
            "role": "user",
            "content": request.question,
            "created_at": datetime.utcnow(),
        }
        assistant_msg = {
            "session_id": session_id,
            "user_id": current_user["_id"],
            "role": "assistant",
            "content": full_answer,
            "references": references_dict if references_dict else None,
            "created_at": datetime.utcnow(),
        }
        
        # Insert messages
        await db.chat_messages.insert_many([user_msg, assistant_msg])
        logger.info(f"✅ Messages saved to MongoDB")
        
        # Create or update chat session
        session_exists = await db.chat_sessions.find_one({
            "session_id": session_id,
            "user_id": current_user["_id"]
        })
        
        if not session_exists:
            # Create new session
            session_doc = {
                "session_id": session_id,
                "user_id": current_user["_id"],
                "title": request.question[:50] + ("..." if len(request.question) > 50 else ""),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
            await db.chat_sessions.insert_one(session_doc)
            logger.info(f"✅ New session created: {session_id}")
        else:
            # Update existing session
            await db.chat_sessions.update_one(
                {"session_id": session_id, "user_id": current_user["_id"]},
                {"$set": {"updated_at": datetime.utcnow()}}
            )
            logger.info(f"✅ Session updated: {session_id}")
        
        # Update Redis cache with new messages
        await redis_service.add_message(
            user_id=str(current_user["_id"]),
            session_id=session_id,
            role="user",
            content=request.question
        )
        await redis_service.add_message(
            user_id=str(current_user["_id"]),
            session_id=session_id,
            role="assistant",
            content=full_answer
        )
        logger.info(f"✅ Messages cached in Redis")
        
    except Exception as e:
        logger.error(f"Streaming error: {e}", exc_info=True)
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    db = Depends(get_database),
    current_user: dict = Depends(get_current_user),
):
    """Stream chat responses in real-time using Server-Sent Events"""
    return StreamingResponse(
        stream_chat_response(request, db, current_user),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )
