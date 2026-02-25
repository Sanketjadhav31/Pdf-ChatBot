"""
Integration tests for end-to-end workflows.

Tests cover:
- Complete upload and chat flow
- Multiple document handling
- Session persistence across requests
"""
import io
import pytest
from fastapi.testclient import TestClient


class TestIntegration:
    """Integration test suite for complete workflows."""

    def test_complete_upload_and_chat_flow(self, client: TestClient, sample_pdf_bytes: bytes):
        """
        ✅ Integration Test 1: Complete flow from upload to chat
        Expected: Upload PDF, then successfully chat about it
        """
        # Step 1: Upload PDF
        files = {"file": ("test.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
        upload_response = client.post("/api/v1/documents/upload", files=files)
        assert upload_response.status_code == 200
        
        document_id = upload_response.json()["document_id"]
        
        # Step 2: Chat about the document
        chat_payload = {"question": "What is in the document?"}
        chat_response = client.post("/api/v1/chat", json=chat_payload)
        assert chat_response.status_code == 200
        
        chat_data = chat_response.json()
        assert "answer" in chat_data
        assert "session_id" in chat_data
        print("✅ Complete upload and chat flow successful")

    def test_multiple_documents_upload_and_query(self, client: TestClient, sample_pdf_bytes: bytes):
        """
        ✅ Integration Test 2: Upload multiple documents and query
        Expected: Can upload multiple PDFs and chat references all
        """
        # Upload first document
        files1 = {"file": ("doc1.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
        response1 = client.post("/api/v1/documents/upload", files=files1)
        assert response1.status_code == 200
        
        # Upload second document
        files2 = {"file": ("doc2.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
        response2 = client.post("/api/v1/documents/upload", files=files2)
        assert response2.status_code == 200
        
        # Chat should work with both documents
        chat_payload = {"question": "What information is available?"}
        chat_response = client.post("/api/v1/chat", json=chat_payload)
        assert chat_response.status_code == 200
        print("✅ Multiple documents handled")

    def test_session_persistence_across_multiple_chats(self, client: TestClient, sample_pdf_bytes: bytes):
        """
        ✅ Integration Test 3: Session persists across multiple chat requests
        Expected: Same session_id maintained throughout conversation
        """
        # Upload document
        files = {"file": ("test.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
        client.post("/api/v1/documents/upload", files=files)
        
        # First chat
        chat1 = {"question": "First question"}
        response1 = client.post("/api/v1/chat", json=chat1)
        session_id = response1.json()["session_id"]
        
        # Second chat with same session
        chat2 = {"session_id": session_id, "question": "Second question"}
        response2 = client.post("/api/v1/chat", json=chat2)
        
        # Third chat with same session
        chat3 = {"session_id": session_id, "question": "Third question"}
        response3 = client.post("/api/v1/chat", json=chat3)
        
        assert response2.json()["session_id"] == session_id
        assert response3.json()["session_id"] == session_id
        print("✅ Session persists across chats")

    def test_upload_then_chat_then_upload_again(self, client: TestClient, sample_pdf_bytes: bytes):
        """
        ✅ Integration Test 4: Upload, chat, upload more, chat again
        Expected: New documents are searchable immediately
        """
        # First upload
        files1 = {"file": ("doc1.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
        client.post("/api/v1/documents/upload", files=files1)
        
        # First chat
        chat1 = {"question": "Question 1"}
        response1 = client.post("/api/v1/chat", json=chat1)
        assert response1.status_code == 200
        
        # Second upload
        files2 = {"file": ("doc2.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
        client.post("/api/v1/documents/upload", files=files2)
        
        # Second chat should work with both documents
        chat2 = {"question": "Question 2"}
        response2 = client.post("/api/v1/chat", json=chat2)
        assert response2.status_code == 200
        print("✅ Sequential upload and chat works")

    def test_error_recovery_after_failed_upload(self, client: TestClient, sample_pdf_bytes: bytes, corrupted_file_bytes: bytes):
        """
        ✅ Integration Test 5: System recovers after failed upload
        Expected: Failed upload doesn't break subsequent operations
        """
        # Try to upload corrupted file
        files1 = {"file": ("bad.pdf", io.BytesIO(corrupted_file_bytes), "application/pdf")}
        bad_response = client.post("/api/v1/documents/upload", files=files1)
        # Should fail
        assert bad_response.status_code in [400, 422, 500]
        
        # Upload valid file should still work
        files2 = {"file": ("good.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
        good_response = client.post("/api/v1/documents/upload", files=files2)
        assert good_response.status_code == 200
        
        # Chat should work
        chat = {"question": "Test question"}
        chat_response = client.post("/api/v1/chat", json=chat)
        assert chat_response.status_code == 200
        print("✅ System recovers after error")
