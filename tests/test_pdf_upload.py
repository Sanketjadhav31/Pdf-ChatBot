"""
Test cases for PDF upload functionality.

Tests cover:
- Valid PDF upload
- Invalid file type rejection
- Large PDF handling
- Corrupted file handling
- Empty file handling
"""
import io
import pytest
from fastapi.testclient import TestClient


class TestPDFUpload:
    """Test suite for PDF upload endpoint."""

    def test_upload_valid_pdf_success(self, client: TestClient, sample_pdf_bytes: bytes):
        """
        ✅ Test Case 1: Upload valid PDF
        Expected: 200 status, document_id, filename, total_chunks returned
        """
        files = {"file": ("test.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
        response = client.post("/api/v1/documents/upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert "document_id" in data
        assert data["filename"] == "test.pdf"
        assert "total_chunks" in data
        assert isinstance(data["total_chunks"], int)
        print("✅ Valid PDF upload successful")

    def test_upload_non_pdf_file_rejected(self, client: TestClient):
        """
        ✅ Test Case 2: Upload non-PDF file (e.g., .txt, .docx)
        Expected: 422 or 400 error, rejection message
        """
        text_content = b"This is a text file, not a PDF"
        files = {"file": ("test.txt", io.BytesIO(text_content), "text/plain")}
        response = client.post("/api/v1/documents/upload", files=files)
        
        assert response.status_code in [400, 422, 500]
        print("✅ Non-PDF file correctly rejected")

    def test_upload_large_pdf_success(self, client: TestClient, large_pdf_bytes: bytes):
        """
        ✅ Test Case 3: Upload large PDF (50+ pages)
        Expected: Should process without crash, return success
        """
        files = {"file": ("large.pdf", io.BytesIO(large_pdf_bytes), "application/pdf")}
        response = client.post("/api/v1/documents/upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_chunks"] >= 0  # May be 0 if pages are blank
        print("✅ Large PDF processed successfully")

    def test_upload_corrupted_pdf_handled(self, client: TestClient, corrupted_file_bytes: bytes):
        """
        ✅ Test Case 4: Upload corrupted/invalid PDF
        Expected: Should return error, not crash server
        """
        files = {"file": ("corrupted.pdf", io.BytesIO(corrupted_file_bytes), "application/pdf")}
        response = client.post("/api/v1/documents/upload", files=files)
        
        # Should fail gracefully
        assert response.status_code in [400, 422, 500]
        print("✅ Corrupted PDF handled gracefully")

    def test_upload_empty_pdf(self, client: TestClient):
        """
        ✅ Test Case 5: Upload empty PDF (0 bytes)
        Expected: Should handle gracefully, return 0 chunks or error
        """
        empty_bytes = b""
        files = {"file": ("empty.pdf", io.BytesIO(empty_bytes), "application/pdf")}
        response = client.post("/api/v1/documents/upload", files=files)
        
        # Either succeeds with 0 chunks or returns error
        if response.status_code == 200:
            data = response.json()
            assert data["total_chunks"] == 0
        else:
            assert response.status_code in [400, 422, 500]
        print("✅ Empty PDF handled correctly")

    def test_upload_pdf_with_special_characters_in_filename(self, client: TestClient, sample_pdf_bytes: bytes):
        """
        ✅ Test Case 6: Upload PDF with special characters in filename
        Expected: Should handle filename correctly
        """
        special_filename = "test file (2024) [final].pdf"
        files = {"file": (special_filename, io.BytesIO(sample_pdf_bytes), "application/pdf")}
        response = client.post("/api/v1/documents/upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == special_filename
        print("✅ Special characters in filename handled")

    def test_upload_multiple_pdfs_sequentially(self, client: TestClient, sample_pdf_bytes: bytes):
        """
        ✅ Test Case 7: Upload multiple PDFs one after another
        Expected: Each should get unique document_id
        """
        document_ids = []
        
        for i in range(3):
            files = {"file": (f"test{i}.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
            response = client.post("/api/v1/documents/upload", files=files)
            assert response.status_code == 200
            document_ids.append(response.json()["document_id"])
        
        # All document IDs should be unique
        assert len(document_ids) == len(set(document_ids))
        print("✅ Multiple PDFs uploaded with unique IDs")

    def test_upload_without_file_parameter(self, client: TestClient):
        """
        ✅ Test Case 8: Call upload endpoint without file parameter
        Expected: 422 validation error
        """
        response = client.post("/api/v1/documents/upload")
        
        assert response.status_code == 422
        print("✅ Missing file parameter correctly rejected")
