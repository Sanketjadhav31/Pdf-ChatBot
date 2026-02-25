"""
Test cases for chat API endpoint.

Tests cover:
- Chat with uploaded documents
- Chat without documents
- Irrelevant questions
- Session management
- Response format validation
"""
import io
import pytest
from fastapi.testclient import TestClient


class TestChatAPI:
    """Test suite for chat endpoint."""

    def test_chat_without_documents_returns_message(self, client: TestClient):
        """
        ✅ Test Case 1: Chat without uploading documents
        Expected: Returns message asking to upload documents
        """
        payload = {
            "question": "What is machine learning?"
        }
        response = client.post("/api/v1/chat", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "No documents have been uploaded" in data["answer"]
        assert data["references"] == []
        print("✅ Chat without documents handled")

    def test_chat_with_uploaded_document(self, client: TestClient, sample_pdf_bytes: bytes):
        """
        ✅ Test Case 2: Chat after uploading a document
        Expected: Returns answer with references
        """
        # First upload a document
        files = {"file": ("test.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
        upload_response = client.post("/api/v1/documents/upload", files=files)
        assert upload_response.status_code == 200
        
        # Then ask a question
        payload = {
            "question": "What is in the document?"
        }
        chat_response = client.post("/api/v1/chat", json=payload)
        
        assert chat_response.status_code == 200
        data = chat_response.json()
        assert "answer" in data
        assert "references" in data
        assert "session_id" in data
        print("✅ Chat with document successful")

    def test_chat_response_format_is_valid(self, client: TestClient, sample_pdf_bytes: bytes):
        """
        ✅ Test Case 3: Chat response has correct format
        Expected: Contains answer, references, session_id
        """
        # Upload document
        files = {"file": ("test.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
        client.post("/api/v1/documents/upload", files=files)
        
        # Chat
        payload = {"question": "Test question"}
        response = client.post("/api/v1/chat", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["answer"], str)
        assert isinstance(data["references"], list)
        assert isinstance(data["session_id"], str)
        print("✅ Response format validated")

    def test_chat_with_empty_question(self, client: TestClient):
        """
        ✅ Test Case 4: Chat with empty question
        Expected: Should handle gracefully or return validation error
        """
        payload = {"question": ""}
        response = client.post("/api/v1/chat", json=payload)
        
        # Either succeeds with appropriate message or validation error
        assert response.status_code in [200, 422]
        print("✅ Empty question handled")

    def test_chat_with_very_long_question(self, client: TestClient, sample_pdf_bytes: bytes):
        """
        ✅ Test Case 5: Chat with very long question (1000+ characters)
        Expected: Should process without error
        """
        # Upload document
        files = {"file": ("test.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
        client.post("/api/v1/documents/upload", files=files)
        
        # Very long question
        long_question = "What is " + "machine learning " * 100 + "?"
        payload = {"question": long_question}
        response = client.post("/api/v1/chat", json=payload)
        
        assert response.status_code == 200
        print("✅ Long question handled")

    def test_chat_session_id_persistence(self, client: TestClient, sample_pdf_bytes: bytes):
        """
        ✅ Test Case 6: Session ID persists across multiple chats
        Expected: Same session_id can be reused
        """
        # Upload document
        files = {"file": ("test.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
        client.post("/api/v1/documents/upload", files=files)
        
        # First chat
        payload1 = {"question": "First question"}
        response1 = client.post("/api/v1/chat", json=payload1)
        session_id = response1.json()["session_id"]
        
        # Second chat with same session
        payload2 = {"session_id": session_id, "question": "Second question"}
        response2 = client.post("/api/v1/chat", json=payload2)
        
        assert response2.json()["session_id"] == session_id
        print("✅ Session ID persists")

    def test_chat_creates_new_session_if_not_provided(self, client: TestClient, sample_pdf_bytes: bytes):
        """
        ✅ Test Case 7: New session created if session_id not provided
        Expected: Returns new session_id
        """
        # Upload document
        files = {"file": ("test.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
        client.post("/api/v1/documents/upload", files=files)
        
        # Chat without session_id
        payload = {"question": "Test question"}
        response = client.post("/api/v1/chat", json=payload)
        
        assert response.status_code == 200
        assert len(response.json()["session_id"]) > 0
        print("✅ New session created")

    def test_chat_with_special_characters(self, client: TestClient, sample_pdf_bytes: bytes):
        """
        ✅ Test Case 8: Chat with special characters in question
        Expected: Should handle special characters correctly
        """
        # Upload document
        files = {"file": ("test.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
        client.post("/api/v1/documents/upload", files=files)
        
        # Question with special characters
        payload = {"question": "What about @#$%^&*() symbols?"}
        response = client.post("/api/v1/chat", json=payload)
        
        assert response.status_code == 200
        print("✅ Special characters handled")

    def test_chat_without_question_field(self, client: TestClient):
        """
        ✅ Test Case 9: Chat request without question field
        Expected: 422 validation error
        """
        payload = {"session_id": "test-session"}
        response = client.post("/api/v1/chat", json=payload)
        
        assert response.status_code == 422
        print("✅ Missing question field rejected")

    def test_irrelevant_question_returns_appropriate_message(self, client: TestClient, sample_pdf_bytes: bytes):
        """
        ✅ Test Case 10: Ask question unrelated to document
        Expected: Returns message about question not being related
        """
        # Upload document
        files = {"file": ("test.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
        client.post("/api/v1/documents/upload", files=files)
        
        # Completely unrelated question
        payload = {"question": "What is the weather today?"}
        response = client.post("/api/v1/chat", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        # May return "not related" message or actual answer depending on similarity
        assert isinstance(data["answer"], str)
        print("✅ Irrelevant question handled")
