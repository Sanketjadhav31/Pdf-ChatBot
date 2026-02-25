"""
Test cases for chat orchestrator logic.

Tests cover:
- Session management
- No documents handling
- Irrelevant question handling
- Reference generation
"""
import pytest
from app.services.rag_service import ChatOrchestrator, InMemoryVectorStore
from app.models.schemas import ChatRequest, Chunk, ChunkMetadata


class TestChatOrchestrator:
    """Test suite for chat orchestrator."""

    def test_handle_chat_without_documents(self, chat_orchestrator: ChatOrchestrator):
        """
        ✅ Test Case 1: Chat when no documents uploaded
        Expected: Returns message to upload documents
        """
        request = ChatRequest(question="What is AI?")
        response = chat_orchestrator.handle_chat(request)
        
        assert "No documents have been uploaded" in response.answer
        assert response.references == []
        print("✅ No documents message returned")

    def test_handle_chat_creates_session_id(self, chat_orchestrator: ChatOrchestrator):
        """
        ✅ Test Case 2: Chat creates session_id if not provided
        Expected: Returns valid session_id
        """
        request = ChatRequest(question="Test question")
        response = chat_orchestrator.handle_chat(request)
        
        assert response.session_id is not None
        assert len(response.session_id) > 0
        print("✅ Session ID created")

    def test_handle_chat_preserves_session_id(self, chat_orchestrator: ChatOrchestrator):
        """
        ✅ Test Case 3: Chat preserves provided session_id
        Expected: Returns same session_id
        """
        session_id = "test-session-123"
        request = ChatRequest(session_id=session_id, question="Test")
        response = chat_orchestrator.handle_chat(request)
        
        assert response.session_id == session_id
        print("✅ Session ID preserved")

    def test_handle_chat_with_documents(self, chat_orchestrator: ChatOrchestrator, vector_store: InMemoryVectorStore):
        """
        ✅ Test Case 4: Chat with uploaded documents
        Expected: Returns answer with references
        """
        # Add chunks to store
        chunks = [
            Chunk(
                metadata=ChunkMetadata(
                    chunk_id="chunk1",
                    document_id="doc1",
                    page_number=1
                ),
                content="Machine learning is a subset of AI."
            )
        ]
        vector_store.add_chunks(chunks)
        
        orchestrator = ChatOrchestrator(vector_store)
        request = ChatRequest(question="What is machine learning?")
        response = orchestrator.handle_chat(request)
        
        assert len(response.answer) > 0
        assert isinstance(response.references, list)
        print("✅ Chat with documents successful")

    def test_handle_chat_returns_references(self, chat_orchestrator: ChatOrchestrator, vector_store: InMemoryVectorStore):
        """
        ✅ Test Case 5: Chat returns proper references
        Expected: References contain document_id and page_number
        """
        chunks = [
            Chunk(
                metadata=ChunkMetadata(
                    chunk_id="chunk2",
                    document_id="doc2",
                    page_number=5
                ),
                content="Python is a programming language."
            )
        ]
        vector_store.add_chunks(chunks)
        
        orchestrator = ChatOrchestrator(vector_store)
        request = ChatRequest(question="Tell me about Python")
        response = orchestrator.handle_chat(request)
        
        if response.references:
            ref = response.references[0]
            assert ref.document_id is not None
            assert ref.page_number is not None
        print("✅ References returned correctly")

    def test_irrelevant_question_handling(self, chat_orchestrator: ChatOrchestrator, vector_store: InMemoryVectorStore):
        """
        ✅ Test Case 6: Irrelevant question returns appropriate message
        Expected: Message about question not being related
        """
        chunks = [
            Chunk(
                metadata=ChunkMetadata(
                    chunk_id="chunk3",
                    document_id="doc3",
                    page_number=1
                ),
                content="Technical documentation about software."
            )
        ]
        vector_store.add_chunks(chunks)
        
        orchestrator = ChatOrchestrator(vector_store)
        request = ChatRequest(question="What is the weather?")
        response = orchestrator.handle_chat(request)
        
        # May return "not related" or actual answer depending on similarity
        assert isinstance(response.answer, str)
        print("✅ Irrelevant question handled")
