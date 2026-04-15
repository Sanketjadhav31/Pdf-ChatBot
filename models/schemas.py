from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class DocumentMetadata(BaseModel):
    document_id: str
    filename: str


class ChunkMetadata(BaseModel):
    chunk_id: str
    document_id: str
    page_number: int
    document_heading: Optional[str] = None
    paragraph_heading: Optional[str] = None

class Chunk(BaseModel):
    metadata: ChunkMetadata
    content: str


class UploadResponse(BaseModel):
    document_id: str
    filename: str
    total_chunks: int


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    question: str
    # Optional list of selected/uploaded document IDs that the user wants
    # to use as the PDF context for this question.
    # When omitted or empty, the backend can still answer casual messages,
    # but document-grounded answers should not assume any PDF context.
    document_ids: Optional[List[str]] = None
    # Optional mapping so backend/RAG can include human-friendly filenames
    # in context markers and PDF-wise explanations.
    document_filenames: Optional[dict[str, str]] = None


class Reference(BaseModel):
    document_id: str
    page_number: int
    document_heading: Optional[str] = None
    paragraph_heading: Optional[str] = None
    # Level 1: show a preview of the text snippet that supported this source.
    snippet: Optional[str] = None
    # Level 1/2: longer snippet for hover/tooltip preview.
    snippet_hover: Optional[str] = None


class PdfScopeDoc(BaseModel):
    document_id: str
    filename: str
    pages: List[int] = Field(default_factory=list)


class PdfScope(BaseModel):
    used: List[PdfScopeDoc] = Field(default_factory=list)
    not_used: List[PdfScopeDoc] = Field(default_factory=list)


class ChatResponse(BaseModel):
    answer: str
    references: List[Reference]
    session_id: str
    # Structured "which PDFs were used vs not used" metadata for this answer.
    # Keep it separate from `answer` so the assistant output stays clean.
    pdf_scope: Optional[PdfScope] = None


class UserOut(BaseModel):
    id: str
    email: EmailStr
    username: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class ChatSessionSummary(BaseModel):
    id: str
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ChatHistoryItem(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime
    attached_docs: List[DocumentMetadata] = Field(default_factory=list)
    references: List[Reference] = Field(default_factory=list)
    # Optional per-message scope metadata (used for multi-PDF chats).
    pdf_scope: Optional[PdfScope] = None


class ChatHistoryResponse(BaseModel):
    session_id: str
    title: Optional[str] = None
    messages: List[ChatHistoryItem]
    # Documents that were used/linked to this chat session.
    documents: List[DocumentMetadata] = Field(default_factory=list)


class UploadedDocumentItem(BaseModel):
    id: str
    filename: str
    created_at: datetime


# Read Mode Schemas
class TextSelection(BaseModel):
    selected_text: str
    page_number: int
    char_start: Optional[int] = None
    char_end: Optional[int] = None


class ReadModeRequest(BaseModel):
    session_id: Optional[str] = None
    document_id: str
    question: str
    selected_text: Optional[str] = None
    page_number: int
    char_start: Optional[int] = None
    char_end: Optional[int] = None


class ReadModeResponse(BaseModel):
    answer: str
    session_id: str


class ReadModeMessage(BaseModel):
    id: str
    role: str  # "user" or "assistant"
    content: str
    selected_text: Optional[str] = None
    page_number: Optional[int] = None
    created_at: datetime


class ReadModeHistoryResponse(BaseModel):
    session_id: str
    document_id: str
    messages: List[ReadModeMessage]


class PageTextResponse(BaseModel):
    page_number: int
    text: str
    total_pages: int

