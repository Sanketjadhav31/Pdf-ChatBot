import uuid

from fastapi import APIRouter, File, UploadFile

from models.schemas import UploadResponse
from services.pdf_loader import extract_chunks_from_pdf
from services.rag_service import vector_store


router = APIRouter(tags=["documents"])


@router.post("/documents/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)) -> UploadResponse:
    """
    Upload a single PDF, extract chunks, and store them in the vector store.
    """
    if file.content_type != "application/pdf":
        raise ValueError("Only PDF files are supported.")

    raw_bytes = await file.read()
    document_id = str(uuid.uuid4())

    chunks = extract_chunks_from_pdf(
        document_id=document_id,
        filename=file.filename,
        file_bytes=raw_bytes,
    )

    vector_store.add_chunks(chunks)

    return UploadResponse(
        document_id=document_id,
        filename=file.filename,
        total_chunks=len(chunks),
    )

