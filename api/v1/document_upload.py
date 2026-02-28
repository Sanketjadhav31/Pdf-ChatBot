import uuid
from pathlib import Path

from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import FileResponse

from models.schemas import UploadResponse
from services.pdf_loader import extract_chunks_from_pdf
from services.rag_service import vector_store

router = APIRouter(tags=["documents"])

# Store uploaded PDFs temporarily
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/documents/upload", response_model=UploadResponse)
async def upload_pdf(
    file: UploadFile = File(...)
) -> UploadResponse:
    """
    Upload a single PDF, save it, and process chunks synchronously.
    Returns after processing is complete so chat can work immediately.
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
        print(f"\n{'='*60}")
        print(f"📄 PROCESSING PDF: {file.filename}")
        print(f"{'='*60}")
        print(f"Document ID: {document_id}")
        print(f"File size: {len(raw_bytes) / 1024:.2f} KB")
        
        print(f"\n🔍 Extracting text chunks from PDF...")
        chunks = extract_chunks_from_pdf(
            document_id=document_id,
            filename=file.filename or "document.pdf",
            file_bytes=raw_bytes,
        )
        print(f"✅ Extracted {len(chunks)} chunks from PDF")
        
        vector_store.add_chunks(chunks)
        
        print(f"\n✨ PDF processing complete!")
        print(f"{'='*60}\n")
        
        return UploadResponse(
            document_id=document_id,
            filename=file.filename or "document.pdf",
            total_chunks=len(chunks),
        )
    except Exception as e:
        print(f"Error processing PDF {file.filename}: {e}")
        # Clean up the saved file if processing failed
        if pdf_path.exists():
            pdf_path.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")


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

