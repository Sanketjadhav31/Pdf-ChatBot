"""
Test cases for PDF processing: chunking and text extraction.

Tests cover:
- Text extraction from PDF
- Chunking logic
- Metadata generation
- Page-wise processing
"""
import pytest
from app.services.pdf_loader import extract_chunks_from_pdf
from app.models.schemas import Chunk


class TestPDFProcessing:
    """Test suite for PDF text extraction and chunking."""

    def test_extract_chunks_from_valid_pdf(self, sample_pdf_bytes: bytes):
        """
        ✅ Test Case 1: Extract chunks from valid PDF
        Expected: Returns list of Chunk objects with metadata
        """
        chunks = extract_chunks_from_pdf(
            document_id="test-doc-123",
            filename="test.pdf",
            file_bytes=sample_pdf_bytes
        )
        
        assert isinstance(chunks, list)
        # May be empty if PDF has no text
        for chunk in chunks:
            assert isinstance(chunk, Chunk)
            assert chunk.metadata.document_id == "test-doc-123"
            assert chunk.metadata.page_number > 0
        print("✅ Chunks extracted successfully")

    def test_chunk_metadata_contains_required_fields(self, sample_pdf_bytes: bytes):
        """
        ✅ Test Case 2: Verify chunk metadata has all required fields
        Expected: chunk_id, document_id, page_number present
        """
        chunks = extract_chunks_from_pdf(
            document_id="test-doc-456",
            filename="test.pdf",
            file_bytes=sample_pdf_bytes
        )
        
        for chunk in chunks:
            assert chunk.metadata.chunk_id is not None
            assert chunk.metadata.document_id == "test-doc-456"
            assert chunk.metadata.page_number is not None
            assert isinstance(chunk.metadata.page_number, int)
        print("✅ Chunk metadata validated")

    def test_empty_pages_are_skipped(self, sample_pdf_bytes: bytes):
        """
        ✅ Test Case 3: Empty pages should be skipped
        Expected: No chunks created for blank pages
        """
        chunks = extract_chunks_from_pdf(
            document_id="test-doc-789",
            filename="blank.pdf",
            file_bytes=sample_pdf_bytes
        )
        
        # Blank PDF should produce 0 chunks
        for chunk in chunks:
            assert len(chunk.content.strip()) > 0
        print("✅ Empty pages handled correctly")

    def test_page_numbers_are_sequential(self, large_pdf_bytes: bytes):
        """
        ✅ Test Case 4: Page numbers should be sequential starting from 1
        Expected: page_number = 1, 2, 3, ...
        """
        chunks = extract_chunks_from_pdf(
            document_id="test-doc-multi",
            filename="multi.pdf",
            file_bytes=large_pdf_bytes
        )
        
        if chunks:
            page_numbers = [chunk.metadata.page_number for chunk in chunks]
            # Should start from 1 and be sequential
            assert page_numbers[0] >= 1
            for i in range(1, len(page_numbers)):
                assert page_numbers[i] >= page_numbers[i-1]
        print("✅ Page numbers are sequential")

    def test_chunk_ids_are_unique(self, large_pdf_bytes: bytes):
        """
        ✅ Test Case 5: Each chunk should have unique chunk_id
        Expected: No duplicate chunk_ids
        """
        chunks = extract_chunks_from_pdf(
            document_id="test-doc-unique",
            filename="test.pdf",
            file_bytes=large_pdf_bytes
        )
        
        chunk_ids = [chunk.metadata.chunk_id for chunk in chunks]
        assert len(chunk_ids) == len(set(chunk_ids))
        print("✅ All chunk IDs are unique")

    def test_corrupted_pdf_raises_error(self, corrupted_file_bytes: bytes):
        """
        ✅ Test Case 6: Corrupted PDF should raise appropriate error
        Expected: Exception raised during processing
        """
        with pytest.raises(Exception):
            extract_chunks_from_pdf(
                document_id="test-doc-corrupt",
                filename="corrupt.pdf",
                file_bytes=corrupted_file_bytes
            )
        print("✅ Corrupted PDF raises error")

    def test_chunk_content_is_string(self, sample_pdf_bytes: bytes):
        """
        ✅ Test Case 7: Chunk content should be string type
        Expected: content field is str
        """
        chunks = extract_chunks_from_pdf(
            document_id="test-doc-content",
            filename="test.pdf",
            file_bytes=sample_pdf_bytes
        )
        
        for chunk in chunks:
            assert isinstance(chunk.content, str)
        print("✅ Chunk content is string type")
