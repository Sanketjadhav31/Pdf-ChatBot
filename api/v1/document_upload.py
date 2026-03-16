import uuid
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from database import UploadedDocument, get_current_user, get_db, User
from models.schemas import UploadResponse, UploadedDocumentItem
from services.pdf_loader import extract_chunks_from_pdf
from services.rag_service import vector_store

router = APIRouter(tags=["documents"])

# Store uploaded PDFs temporarily
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/documents/upload", response_model=UploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UploadResponse:
    """
    Upload a single PDF, save it, and process chunks synchronously.
    Returns after processing is complete so chat can work immediately.

    This endpoint is intentionally synchronous so the frontend can show
    real progress and immediately start chatting with the uploaded file.
    Large PDFs are automatically down-sampled instead of failing with
    an error, so users can still work with long documents.
    """
    if file.content_type != "application/pdf":
        raise ValueError("Only PDF files are supported.")

    raw_bytes = await file.read()
    document_id = str(uuid.uuid4())

    # Save PDF file for viewing
    pdf_path = UPLOAD_DIR / f"{document_id}.pdf"
    with open(pdf_path, "wb") as f:
        f.write(raw_bytes)

    # Process chunks synchronously - wait for completion
    # This ensures the vector store is ready before returning
    try:
        print(f"PROCESSING PDF: {file.filename}")
        print(f"Document ID: {document_id}")
        print(f"File size: {len(raw_bytes) / 1024:.2f} KB")
        
        print(f"\n🔍 Extracting text chunks from PDF...")
        chunks = extract_chunks_from_pdf(
            document_id=document_id,
            filename=file.filename or "document.pdf",
            file_bytes=raw_bytes,
        )
        print(f"✅ Extracted {len(chunks)} chunks from PDF")

        # Hard limit to avoid very large PDFs exhausting embedding quota.
        # For very long PDFs we *down-sample* the chunks instead of failing
        # the upload, so the user can still chat with a representative
        # summary of the document.
        MAX_CHUNKS = 200
        if len(chunks) > MAX_CHUNKS:
            print(f"PDF too large: {len(chunks)} chunks (limit {MAX_CHUNKS})")
            # Keep a representative sample of chunks spread across the document.
            # This preserves coverage from beginning, middle and end while
            # respecting the quota-friendly limit.
            step = max(len(chunks) // MAX_CHUNKS, 1)
            sampled_chunks = [chunks[i] for i in range(0, len(chunks), step)]
            if len(sampled_chunks) > MAX_CHUNKS:
                sampled_chunks = sampled_chunks[:MAX_CHUNKS]
            print(
                f"Down-sampling chunks: original={len(chunks)}, "
                f"sampled={len(sampled_chunks)}, step={step}"
            )
            chunks = sampled_chunks

        vector_store.add_chunks(chunks)

        # Persist uploaded document metadata for history
        db_doc = UploadedDocument(
            id=document_id,
            user_id=current_user.id,
            filename=file.filename or "document.pdf",
            stored_path=str(pdf_path),
        )
        db.add(db_doc)
        db.commit()
        
        print(f"\n✨ PDF processing complete!")
        print(f"{'='*60}\n")
        
        return UploadResponse(
            document_id=document_id,
            filename=file.filename or "document.pdf",
            total_chunks=len(chunks),
        )
    except Exception as e:
        print(f"Error processing PDF {file.filename}: {e}")
        message = str(e)

        # Surface quota issues more clearly
        if "RESOURCE_EXHAUSTED" in message or "rate-limits" in message:
            if pdf_path.exists():
                pdf_path.unlink()
            raise HTTPException(
                status_code=429,
                detail=(
                    "The PDF is large and embedding exceeded the current AI quota. "
                    "Please wait a bit and try again, or use a smaller document."
                ),
            )

        # Clean up the saved file if processing failed
        if pdf_path.exists():
            pdf_path.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {message}")


@router.get("/documents/{document_id}/view")
async def view_pdf(document_id: str):
    """
    View a PDF document by its ID.
    """
    pdf_path = UPLOAD_DIR / f"{document_id}.pdf"
    
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="Document not found")
    
    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "inline",
            "Cache-Control": "public, max-age=3600",
            "Accept-Ranges": "bytes"
        }
    )


@router.get("/documents", response_model=list[UploadedDocumentItem])
async def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List uploaded PDFs for the current user from the last 1 day.
    """
    cutoff = datetime.utcnow() - timedelta(days=1)
    docs = (
        db.query(UploadedDocument)
        .filter(
            UploadedDocument.user_id == current_user.id,
            UploadedDocument.created_at >= cutoff,
        )
        .order_by(UploadedDocument.created_at.desc())
        .all()
    )
    return [
        UploadedDocumentItem(
            id=d.id,
            filename=d.filename,
            created_at=d.created_at,
        )
        for d in docs
    ]



@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a document and its associated chunks from the vector store.
    """
    # Find the document in the database
    doc = (
        db.query(UploadedDocument)
        .filter(
            UploadedDocument.id == document_id,
            UploadedDocument.user_id == current_user.id,
        )
        .first()
    )
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete the PDF file from disk
    pdf_path = UPLOAD_DIR / f"{document_id}.pdf"
    if pdf_path.exists():
        pdf_path.unlink()
    
    # Delete chunks from vector store
    vector_store.delete_chunks_by_document(document_id)
    
    # Delete from database
    db.delete(doc)
    db.commit()
    
    return {"message": "Document deleted successfully", "document_id": document_id}
