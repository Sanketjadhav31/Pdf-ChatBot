from io import BytesIO
from typing import List

from PyPDF2 import PdfReader

from models.schemas import Chunk, ChunkMetadata


def extract_chunks_from_pdf(
    document_id: str,
    filename: str,
    file_bytes: bytes,
) -> List[Chunk]:
    """
    Basic PDF text extraction and chunking.

    For step 1 we:
    - extract page-wise text
    - treat each page as a single chunk
    - attach page_number metadata

    Later this can be enhanced with heading detection and smarter chunking.
    """
    pdf_reader = PdfReader(BytesIO(file_bytes))
    total_pages = len(pdf_reader.pages)
    print(f"📖 Total pages in PDF: {total_pages}")

    chunks: List[Chunk] = []
    for page_index, page in enumerate(pdf_reader.pages):
        # Show progress every 25 pages or on last page for faster processing
        if (page_index + 1) % 25 == 0 or (page_index + 1) == total_pages:
            progress = ((page_index + 1) / total_pages) * 100
            print(f"   Extracting page {page_index + 1}/{total_pages} ({progress:.1f}%)")
        
        text = page.extract_text() or ""
        cleaned = text.strip()
        if not cleaned:
            continue

        metadata = ChunkMetadata(
            chunk_id=f"{document_id}_page_{page_index + 1}",
            document_id=document_id,
            page_number=page_index + 1,
        )
        chunks.append(
            Chunk(
                metadata=metadata,
                content=cleaned,
            )
        )

    return chunks

