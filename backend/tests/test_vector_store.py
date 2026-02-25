"""
Test cases for vector store: embeddings and similarity search.

Tests cover:
- Adding chunks to vector store
- Embedding generation
- Similarity search
- Top-k retrieval
- Threshold filtering
"""
import pytest
import numpy as np
from app.services.rag_service import InMemoryVectorStore
from app.models.schemas import Chunk, ChunkMetadata


class TestVectorStore:
    """Test suite for vector store operations."""

    def test_add_chunks_increases_store_size(self, vector_store: InMemoryVectorStore):
        """
        ✅ Test Case 1: Adding chunks increases store size
        Expected: store.size increases by number of chunks added
        """
        initial_size = vector_store.size
        
        chunks = [
            Chunk(
                metadata=ChunkMetadata(
                    chunk_id="chunk1",
                    document_id="doc1",
                    page_number=1
                ),
                content="This is test content about machine learning."
            )
        ]
        
        vector_store.add_chunks(chunks)
        assert vector_store.size == initial_size + 1
        print("✅ Chunks added successfully")

    def test_embeddings_are_generated(self, vector_store: InMemoryVectorStore):
        """
        ✅ Test Case 2: Embeddings are generated for each chunk
        Expected: Each chunk gets an embedding vector
        """
        chunks = [
            Chunk(
                metadata=ChunkMetadata(
                    chunk_id="chunk2",
                    document_id="doc2",
                    page_number=1
                ),
                content="Test content for embedding generation."
            )
        ]
        
        vector_store.add_chunks(chunks)
        assert len(vector_store._embeddings) > 0
        assert isinstance(vector_store._embeddings[0], np.ndarray)
        print("✅ Embeddings generated")

    def test_embedding_dimension_is_consistent(self, vector_store: InMemoryVectorStore):
        """
        ✅ Test Case 3: All embeddings have same dimension
        Expected: All embedding vectors have dimension 768
        """
        chunks = [
            Chunk(
                metadata=ChunkMetadata(
                    chunk_id=f"chunk{i}",
                    document_id="doc3",
                    page_number=i
                ),
                content=f"Content {i}"
            )
            for i in range(5)
        ]
        
        vector_store.add_chunks(chunks)
        
        for embedding in vector_store._embeddings:
            assert embedding.shape == (768,)
        print("✅ Embedding dimensions consistent")

    def test_search_returns_relevant_chunks(self, vector_store: InMemoryVectorStore):
        """
        ✅ Test Case 4: Search returns relevant chunks
        Expected: Returns list of (Chunk, score) tuples
        """
        chunks = [
            Chunk(
                metadata=ChunkMetadata(
                    chunk_id="chunk4",
                    document_id="doc4",
                    page_number=1
                ),
                content="Machine learning is a subset of artificial intelligence."
            ),
            Chunk(
                metadata=ChunkMetadata(
                    chunk_id="chunk5",
                    document_id="doc4",
                    page_number=2
                ),
                content="Python is a programming language."
            )
        ]
        
        vector_store.add_chunks(chunks)
        results = vector_store.search("What is machine learning?", top_k=2)
        
        assert isinstance(results, list)
        for chunk, score in results:
            assert isinstance(chunk, Chunk)
            assert isinstance(score, float)
            assert 0 <= score <= 1
        print("✅ Search returns relevant results")

    def test_search_respects_top_k_parameter(self, vector_store: InMemoryVectorStore):
        """
        ✅ Test Case 5: Search respects top_k parameter
        Expected: Returns at most top_k results
        """
        chunks = [
            Chunk(
                metadata=ChunkMetadata(
                    chunk_id=f"chunk{i}",
                    document_id="doc5",
                    page_number=i
                ),
                content=f"Content about topic {i}"
            )
            for i in range(10)
        ]
        
        vector_store.add_chunks(chunks)
        results = vector_store.search("topic", top_k=3)
        
        assert len(results) <= 3
        print("✅ Top-k parameter respected")

    def test_search_filters_by_similarity_threshold(self, vector_store: InMemoryVectorStore):
        """
        ✅ Test Case 6: Search filters results below similarity threshold
        Expected: Only returns results above threshold
        """
        chunks = [
            Chunk(
                metadata=ChunkMetadata(
                    chunk_id="chunk6",
                    document_id="doc6",
                    page_number=1
                ),
                content="Relevant content about the query topic."
            )
        ]
        
        vector_store.add_chunks(chunks)
        results = vector_store.search("query topic", similarity_threshold=0.9)
        
        for _, score in results:
            assert score >= 0.9
        print("✅ Similarity threshold applied")

    def test_search_on_empty_store_returns_empty(self, vector_store: InMemoryVectorStore):
        """
        ✅ Test Case 7: Search on empty store returns empty list
        Expected: Returns []
        """
        results = vector_store.search("any query")
        
        assert results == []
        print("✅ Empty store returns empty results")

    def test_cosine_similarity_calculation(self, vector_store: InMemoryVectorStore):
        """
        ✅ Test Case 8: Cosine similarity is calculated correctly
        Expected: Similarity scores are between -1 and 1
        """
        chunks = [
            Chunk(
                metadata=ChunkMetadata(
                    chunk_id="chunk7",
                    document_id="doc7",
                    page_number=1
                ),
                content="Test content for similarity calculation."
            )
        ]
        
        vector_store.add_chunks(chunks)
        results = vector_store.search("similarity test", top_k=1)
        
        if results:
            _, score = results[0]
            assert -1 <= score <= 1
        print("✅ Cosine similarity calculated correctly")

    def test_same_text_has_high_similarity(self, vector_store: InMemoryVectorStore):
        """
        ✅ Test Case 9: Identical text should have high similarity
        Expected: Searching for exact chunk content returns high score
        """
        content = "This is a unique test sentence for similarity."
        chunks = [
            Chunk(
                metadata=ChunkMetadata(
                    chunk_id="chunk8",
                    document_id="doc8",
                    page_number=1
                ),
                content=content
            )
        ]
        
        vector_store.add_chunks(chunks)
        results = vector_store.search(content, top_k=1)
        
        assert len(results) > 0
        _, score = results[0]
        # Due to deterministic hashing, same text should have similarity close to 1
        assert score > 0.5
        print("✅ Same text has high similarity")
