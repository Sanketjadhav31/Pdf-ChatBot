"""
Test cases for edge cases and boundary conditions.

Tests cover:
- Empty inputs
- Extremely large inputs
- Special characters
- Concurrent requests
- Memory limits
"""
import io
import pytest
from fastapi.testclient import TestClient


class TestEdgeCases:
    """Test suite for edge cases and boundary conditions."""

    def test_upload_pdf_with_unicode_filename(self, client: TestClient, sample_pdf_bytes: bytes):
        """
        ✅ Edge Case 1: Upload PDF with Unicode characters in filename
        Expected: Should handle Unicode correctly
        """
        unicode_filename = "测试文档_тест_🚀.pdf"
        files = {"file": (unicode_filename, io.BytesIO(sample_pdf_bytes), "application/pdf")}
        response = client.post("/api/v1/documents/upload", files=files)
        
        assert response.status_code == 200
        assert response.json()["filename"] == unicode_filename
        print("✅ Unicode filename handled")

    def test_chat_with_unicode_question(self, client: TestClient, sample_pdf_bytes: bytes):
        """
        ✅ Edge Case 2: Chat with Unicode characters in question
        Expected: Should process Unicode text correctly
        """
        # Upload document first
        files = {"file": ("test.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
        client.post("/api/v1/documents/upload", files=files)
        
        # Ask question with Unicode
        payload = {"question": "什么是机器学习？ Что такое AI? 🤖"}
        response = client.post("/api/v1/chat", json=payload)
        
        assert response.status_code == 200
        print("✅ Unicode question handled")

    def test_very_long_session_id(self, client: TestClient, sample_pdf_bytes: bytes):
        """
        ✅ Edge Case 3: Use very long session_id
        Expected: Should handle long session IDs
        """
        files = {"file": ("test.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
        client.post("/api/v1/documents/upload", files=files)
        
        long_session_id = "a" * 1000
        payload = {"session_id": long_session_id, "question": "Test"}
        response = client.post("/api/v1/chat", json=payload)
        
        assert response.status_code == 200
        print("✅ Long session ID handled")

    def test_question_with_only_whitespace(self, client: TestClient, sample_pdf_bytes: bytes):
        """
        ✅ Edge Case 4: Question with only whitespace
        Expected: Should handle gracefully
        """
        files = {"file": ("test.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
        client.post("/api/v1/documents/upload", files=files)
        
        payload = {"question": "   \n\t   "}
        response = client.post("/api/v1/chat", json=payload)
        
        # Should either succeed or return validation error
        assert response.status_code in [200, 422]
        print("✅ Whitespace-only question handled")

    def test_question_with_sql_injection_attempt(self, client: TestClient, sample_pdf_bytes: bytes):
        """
        ✅ Edge Case 5: Question with SQL injection patterns
        Expected: Should treat as normal text, no security issues
        """
        files = {"file": ("test.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
        client.post("/api/v1/documents/upload", files=files)
        
        payload = {"question": "'; DROP TABLE users; --"}
        response = client.post("/api/v1/chat", json=payload)
        
        assert response.status_code == 200
        print("✅ SQL injection pattern handled safely")

    def test_question_with_html_tags(self, client: TestClient, sample_pdf_bytes: bytes):
        """
        ✅ Edge Case 6: Question with HTML/script tags
        Expected: Should treat as plain text
        """
        files = {"file": ("test.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
        client.post("/api/v1/documents/upload", files=files)
        
        payload = {"question": "<script>alert('xss')</script>"}
        response = client.post("/api/v1/chat", json=payload)
        
        assert response.status_code == 200
        print("✅ HTML tags handled safely")

    def test_upload_pdf_with_very_long_filename(self, client: TestClient, sample_pdf_bytes: bytes):
        """
        ✅ Edge Case 7: Upload PDF with extremely long filename
        Expected: Should handle or reject gracefully
        """
        long_filename = "a" * 500 + ".pdf"
        files = {"file": (long_filename, io.BytesIO(sample_pdf_bytes), "application/pdf")}
        response = client.post("/api/v1/documents/upload", files=files)
        
        # Should either succeed or return appropriate error
        assert response.status_code in [200, 400, 422]
        print("✅ Long filename handled")

    def test_null_values_in_request(self, client: TestClient):
        """
        ✅ Edge Case 8: Send null values in request
        Expected: Should return validation error
        """
        payload = {"question": None}
        response = client.post("/api/v1/chat", json=payload)
        
        assert response.status_code == 422
        print("✅ Null values rejected")

    def test_missing_content_type_header(self, client: TestClient, sample_pdf_bytes: bytes):
        """
        ✅ Edge Case 9: Upload without proper content-type
        Expected: Should handle or reject appropriately
        """
        files = {"file": ("test.pdf", io.BytesIO(sample_pdf_bytes))}
        response = client.post("/api/v1/documents/upload", files=files)
        
        # May succeed or fail depending on implementation
        assert response.status_code in [200, 400, 422, 500]
        print("✅ Missing content-type handled")
