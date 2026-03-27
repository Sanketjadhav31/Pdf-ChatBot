import asyncio
import os
import uuid
from datetime import datetime, timedelta
from io import BytesIO

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import StreamingResponse

from database import get_current_user, get_database, get_gridfs
from models.schemas import UploadResponse, UploadedDocumentItem
from services.pdf_loader import extract_chunks_from_pdf
from services.rag_service import vector_store
from logger_config import setup_logger, PerformanceTimer, log_step

logger = setup_logger(__name__)
router = APIRouter(tags=["documents"])

# Prevent too many concurrent uploads from queueing inside MongoDB/embedding calls.
# This is the main cause of the "9-10s per file" feeling when you upload many PDFs at once.
UPLOAD_CONCURRENCY = int(os.getenv("UPLOAD_CONCURRENCY", "2"))
upload_processing_semaphore = asyncio.Semaphore(UPLOAD_CONCURRENCY)


@router.post("/documents/upload", response_model=UploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    db = Depends(get_database),
    gridfs = Depends(get_gridfs),
    current_user: dict = Depends(get_current_user),
) -> UploadResponse:
    """
    Upload a single PDF, save it to GridFS, and process chunks synchronously.
    Returns after processing is complete so chat can work immediately.
    """
    if file.content_type != "application/pdf":
        raise ValueError("Only PDF files are supported.")

    raw_bytes = await file.read()
    document_id = str(uuid.uuid4())

    # Process chunks synchronously (bounded by upload_processing_semaphore)
    gridfs_file_id = None

    async with upload_processing_semaphore:
        with PerformanceTimer(logger, f"PDF Upload & Processing: {file.filename}"):
            try:
                log_step(
                    logger,
                    "PDF Upload Started",
                    {
                        "Filename": file.filename,
                        "Document ID": document_id,
                        "File size": f"{len(raw_bytes) / 1024:.2f} KB",
                    },
                )

                # Upload PDF to GridFS
                with PerformanceTimer(logger, "Upload to GridFS"):
                    gridfs_file_id = await gridfs.upload_from_stream(
                        filename=file.filename or "document.pdf",
                        source=BytesIO(raw_bytes),
                        metadata={
                            "document_id": document_id,
                            "user_id": current_user["_id"],
                            "content_type": "application/pdf",
                            "original_filename": file.filename
                            or "document.pdf",
                        },
                    )
                log_step(
                    logger,
                    "GridFS Upload Complete",
                    {"GridFS ID": str(gridfs_file_id)},
                )

                # Extract text chunks
                with PerformanceTimer(logger, "Text Extraction from PDF"):
                    chunks = extract_chunks_from_pdf(
                        document_id=document_id,
                        filename=file.filename or "document.pdf",
                        file_bytes=raw_bytes,
                    )
                log_step(
                    logger,
                    "Text Extraction Complete",
                    {"Total chunks": len(chunks)},
                )

                # Hard limit to avoid very large PDFs exhausting embedding quota
                MAX_CHUNKS = int(os.getenv("MAX_PDF_CHUNKS", "400"))
                if len(chunks) > MAX_CHUNKS:
                    logger.warning(
                        f"PDF too large: {len(chunks)} chunks (limit: {MAX_CHUNKS})"
                    )
                    logger.info("Sampling chunks to fit within limit...")
                    step = max(len(chunks) // MAX_CHUNKS, 1)
                    sampled_chunks = [
                        chunks[i] for i in range(0, len(chunks), step)
                    ]
                    if len(sampled_chunks) > MAX_CHUNKS:
                        sampled_chunks = sampled_chunks[:MAX_CHUNKS]
                    logger.info(
                        f"Down-sampling: original={len(chunks)}, "
                        f"sampled={len(sampled_chunks)}, step={step}"
                    )
                    chunks = sampled_chunks

                # Store chunks in vector store with embeddings
                with PerformanceTimer(
                    logger, "Generate Embeddings & Store in Vector DB"
                ):
                    vector_store.add_chunks(chunks)

                log_step(
                    logger,
                    "Vector Store Updated",
                    {
                        "Chunks stored": len(chunks),
                        "Total vectors": vector_store.size,
                    },
                )

                # Persist uploaded document metadata
                with PerformanceTimer(logger, "Save Metadata to Database"):
                    db_doc = {
                        "_id": document_id,
                        "user_id": current_user["_id"],
                        "filename": file.filename or "document.pdf",
                        "gridfs_file_id": str(gridfs_file_id),
                        "file_size": len(raw_bytes),
                        "created_at": datetime.utcnow()
                        + timedelta(hours=5, minutes=30),
                    }
                    await db.uploaded_documents.insert_one(db_doc)

                log_step(
                    logger,
                    "Upload Complete",
                    {
                        "Document ID": document_id,
                        "Chunks stored": len(chunks),
                    },
                )

                return UploadResponse(
                    document_id=document_id,
                    filename=file.filename or "document.pdf",
                    total_chunks=len(chunks),
                )
            except Exception as e:
                logger.error(f"Error processing PDF: {file.filename}")
                logger.error(f"Error details: {str(e)}", exc_info=True)
                message = str(e)

                # Surface quota issues more clearly
                if "RESOURCE_EXHAUSTED" in message or "rate-limits" in message:
                    # Clean up GridFS file if it was uploaded
                    if gridfs_file_id:
                        try:
                            await gridfs.delete(gridfs_file_id)
                            logger.info(
                                f"Cleaned up GridFS file: {gridfs_file_id}"
                            )
                        except Exception as cleanup_error:
                            logger.error(
                                f"Failed to cleanup GridFS file: {cleanup_error}"
                            )
                    raise HTTPException(
                        status_code=429,
                        detail=(
                            "The PDF is large and embedding exceeded the current AI quota. "
                            "Please wait a bit and try again, or use a smaller document."
                        ),
                    )

                # Clean up GridFS file if processing failed
                if gridfs_file_id:
                    try:
                        await gridfs.delete(gridfs_file_id)
                        logger.info(
                            f"Cleaned up GridFS file: {gridfs_file_id}"
                        )
                    except Exception as cleanup_error:
                        logger.error(
                            f"Failed to cleanup GridFS file: {cleanup_error}"
                        )
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to process PDF: {message}",
                )


@router.get("/documents/{document_id}/view")
async def view_pdf(
    document_id: str,
    db = Depends(get_database),
    gridfs = Depends(get_gridfs),
    current_user: dict = Depends(get_current_user),
):
    """
    View a PDF document by its ID from GridFS.
    """
    # Find the document metadata
    doc = await db.uploaded_documents.find_one({
        "_id": document_id,
        "user_id": current_user["_id"]
    })
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Get GridFS file ID
    gridfs_file_id = doc.get("gridfs_file_id")
    if not gridfs_file_id:
        raise HTTPException(status_code=404, detail="PDF file not found in storage")
    
    try:
        from bson import ObjectId
        # Download file from GridFS
        grid_out = await gridfs.open_download_stream(ObjectId(gridfs_file_id))
        file_data = await grid_out.read()
        
        # Return as streaming response
        return StreamingResponse(
            BytesIO(file_data),
            media_type="application/pdf",
            headers={
                "Content-Disposition": "inline",
                "Cache-Control": "public, max-age=3600",
            }
        )
    except Exception as e:
        print(f"❌ Error retrieving PDF from GridFS: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve PDF")


@router.get("/documents", response_model=list[UploadedDocumentItem])
async def list_documents(
    db = Depends(get_database),
    current_user: dict = Depends(get_current_user),
):
    """
    List uploaded PDFs for the current user.
    """
    cutoff = datetime.utcnow() - timedelta(days=30) + timedelta(hours=5, minutes=30)
    docs = await db.uploaded_documents.find({
        "user_id": current_user["_id"],
        "created_at": {"$gte": cutoff}
    }).sort("created_at", -1).to_list(length=None)
    
    return [
        UploadedDocumentItem(
            id=d["_id"],
            filename=d["filename"],
            created_at=d["created_at"],
        )
        for d in docs
    ]


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    db = Depends(get_database),
    gridfs = Depends(get_gridfs),
    current_user: dict = Depends(get_current_user),
):
    """
    Delete a document and its associated chunks from the vector store and GridFS.
    """
    # Find the document in the database
    doc = await db.uploaded_documents.find_one({
        "_id": document_id,
        "user_id": current_user["_id"]
    })
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete the PDF file from GridFS
    gridfs_file_id = doc.get("gridfs_file_id")
    if gridfs_file_id:
        try:
            from bson import ObjectId
            await gridfs.delete(ObjectId(gridfs_file_id))
            print(f"✅ Deleted PDF from GridFS (ID: {gridfs_file_id})")
        except Exception as e:
            print(f"⚠️  Failed to delete PDF from GridFS: {e}")
    
    # Delete chunks from vector store
    vector_store.delete_chunks_by_document(document_id)
    
    # Delete from database
    await db.uploaded_documents.delete_one({"_id": document_id})
    
    return {"message": "Document deleted successfully", "document_id": document_id}
