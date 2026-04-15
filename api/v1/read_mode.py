"""
Read Mode API - Handles text selection-based PDF reading assistance.

This is completely separate from the RAG chat API. No vector search,
no embeddings - just direct context from selected text.
"""

from datetime import datetime, timedelta
from typing import List
import uuid

from fastapi import APIRouter, Depends, HTTPException

from database import get_current_user, get_database, get_gridfs
from models.schemas import (
    ReadModeRequest,
    ReadModeResponse,
    ReadModeMessage,
    ReadModeHistoryResponse,
    PageTextResponse,
)
from services.read_mode_service import read_mode_service
from services.llm_service import llm_service
from logger_config import setup_logger, PerformanceTimer

logger = setup_logger(__name__)
router = APIRouter(tags=["read-mode"])


@router.post("/read-mode/chat", response_model=ReadModeResponse)
async def read_mode_chat(
    request: ReadModeRequest,
    db = Depends(get_database),
    gridfs = Depends(get_gridfs),
    current_user: dict = Depends(get_current_user),
) -> ReadModeResponse:
    """
    Handle Read Mode chat - answer questions based on selected text.
    
    This endpoint:
    1. Extracts page context from the PDF
    2. Loads conversation history
    3. Builds 3-layer context (selection + page + history)
    4. Generates answer using LLM
    5. Stores message with selection metadata
    """
    with PerformanceTimer(logger, f"Read Mode Chat: {request.question[:50]}..."):
        # Get or create session
        session_id = request.session_id or str(uuid.uuid4())
        
        log_step(logger, "Read Mode Request Received", {
            "User": current_user.get('username', 'Unknown'),
            "Session": session_id,
            "Document": request.document_id,
            "Page": request.page_number,
            "Question": request.question[:100],
            "Has Selection": bool(request.selected_text),
        })
        
        # Verify document ownership
        doc = await db.uploaded_documents.find_one({
            "_id": request.document_id,
            "user_id": current_user["_id"]
        })
        
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Ensure session exists
        session = await db.read_mode_sessions.find_one({
            "_id": session_id,
            "user_id": current_user["_id"]
        })
        
        if not session:
            await db.read_mode_sessions.insert_one({
                "_id": session_id,
                "user_id": current_user["_id"],
                "document_id": request.document_id,
                "created_at": datetime.utcnow() + timedelta(hours=5, minutes=30),
                "updated_at": datetime.utcnow() + timedelta(hours=5, minutes=30),
            })
        else:
            # Update session timestamp
            await db.read_mode_sessions.update_one(
                {"_id": session_id},
                {"$set": {"updated_at": datetime.utcnow() + timedelta(hours=5, minutes=30)}}
            )
        
        # Extract page text from PDF
        gridfs_file_id = doc.get("gridfs_file_id")
        if not gridfs_file_id:
            raise HTTPException(status_code=500, detail="PDF file not found in storage")
        
        try:
            page_text, total_pages = await read_mode_service.extract_page_text(
                gridfs=gridfs,
                gridfs_file_id=gridfs_file_id,
                page_number=request.page_number
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Error extracting page text: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to extract page text")
        
        # Load conversation history (last 3 turns = 6 messages)
        history_messages = await db.read_mode_messages.find({
            "session_id": session_id,
            "user_id": current_user["_id"]
        }).sort("created_at", -1).limit(6).to_list(length=6)
        
        history_messages = list(reversed(history_messages))
        history = [
            {
                "role": m["role"],
                "content": m["content"],
                "selected_text": m.get("selected_text"),
                "page_number": m.get("page_number"),
            }
            for m in history_messages
        ]
        
        # Build 3-layer context
        context = read_mode_service.build_read_mode_context(
            selected_text=request.selected_text,
            page_text=page_text,
            history=history,
            max_history_turns=3
        )
        
        # Generate answer
        answer = await llm_service.generate_read_mode_response(
            prompt=request.question,
            context=context,
            username=current_user["username"]
        )
        
        # Store user message
        user_msg = {
            "_id": str(uuid.uuid4()),
            "session_id": session_id,
            "user_id": current_user["_id"],
            "role": "user",
            "content": request.question,
            "selected_text": request.selected_text,
            "page_number": request.page_number,
            "char_start": request.char_start,
            "char_end": request.char_end,
            "created_at": datetime.utcnow() + timedelta(hours=5, minutes=30),
        }
        
        # Store assistant message
        assistant_msg = {
            "_id": str(uuid.uuid4()),
            "session_id": session_id,
            "user_id": current_user["_id"],
            "role": "assistant",
            "content": answer,
            "selected_text": None,
            "page_number": request.page_number,
            "created_at": datetime.utcnow() + timedelta(hours=5, minutes=30),
        }
        
        await db.read_mode_messages.insert_many([user_msg, assistant_msg])
        
        logger.info(f"Read Mode response complete: {len(answer)} chars")
        
        return ReadModeResponse(
            answer=answer,
            session_id=session_id
        )


@router.get("/read-mode/page-text/{document_id}/{page_number}", response_model=PageTextResponse)
async def get_page_text(
    document_id: str,
    page_number: int,
    db = Depends(get_database),
    gridfs = Depends(get_gridfs),
    current_user: dict = Depends(get_current_user),
) -> PageTextResponse:
    """
    Get text content of a specific page from a PDF.
    
    This is useful for:
    - Displaying page text alongside PDF
    - Providing context for text selection
    - Debugging text extraction
    """
    # Verify document ownership
    doc = await db.uploaded_documents.find_one({
        "_id": document_id,
        "user_id": current_user["_id"]
    })
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    gridfs_file_id = doc.get("gridfs_file_id")
    if not gridfs_file_id:
        raise HTTPException(status_code=500, detail="PDF file not found in storage")
    
    try:
        page_text, total_pages = await read_mode_service.extract_page_text(
            gridfs=gridfs,
            gridfs_file_id=gridfs_file_id,
            page_number=page_number
        )
        
        return PageTextResponse(
            page_number=page_number,
            text=page_text,
            total_pages=total_pages
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error extracting page text: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to extract page text")


@router.get("/read-mode/sessions/{session_id}", response_model=ReadModeHistoryResponse)
async def get_read_mode_session(
    session_id: str,
    db = Depends(get_database),
    current_user: dict = Depends(get_current_user),
) -> ReadModeHistoryResponse:
    """
    Get Read Mode session history with all messages and their selection context.
    """
    session = await db.read_mode_sessions.find_one({
        "_id": session_id,
        "user_id": current_user["_id"]
    })
    
    if not session:
        raise HTTPException(status_code=404, detail="Read Mode session not found")
    
    messages = await db.read_mode_messages.find({
        "session_id": session_id,
        "user_id": current_user["_id"]
    }).sort("created_at", 1).to_list(length=None)
    
    return ReadModeHistoryResponse(
        session_id=session["_id"],
        document_id=session["document_id"],
        messages=[
            ReadModeMessage(
                id=m["_id"],
                role=m["role"],
                content=m["content"],
                selected_text=m.get("selected_text"),
                page_number=m.get("page_number"),
                created_at=m["created_at"],
            )
            for m in messages
        ]
    )


@router.delete("/read-mode/sessions/{session_id}")
async def delete_read_mode_session(
    session_id: str,
    db = Depends(get_database),
    current_user: dict = Depends(get_current_user),
):
    """
    Delete a Read Mode session and all its messages.
    """
    session = await db.read_mode_sessions.find_one({
        "_id": session_id,
        "user_id": current_user["_id"]
    })
    
    if not session:
        raise HTTPException(status_code=404, detail="Read Mode session not found")
    
    # Delete messages
    await db.read_mode_messages.delete_many({"session_id": session_id})
    
    # Delete session
    await db.read_mode_sessions.delete_one({"_id": session_id})
    
    return {"ok": True}


def log_step(logger, step_name: str, details: dict):
    """Helper to log structured step information"""
    logger.info(f"\n{'='*60}")
    logger.info(f"📍 {step_name}")
    logger.info(f"{'='*60}")
    for key, value in details.items():
        logger.info(f"  {key}: {value}")
    logger.info(f"{'='*60}\n")
