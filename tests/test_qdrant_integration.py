"""
Comprehensive Qdrant Integration Tests

Tests cover:
- Qdrant connection and health
- Collection creation and management
- Adding and retrieving chunks
- Semantic search functionality
- Document filtering
- Deletion operations
"""
import pytest
import os
from typing import List
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from models.schemas import Chunk, ChunkMetadata
from services.qdrant_service import QdrantVectorStore
from services.embedding_service import embedding_service


class TestQdrantConnection:
    """Test Qdrant server connection and basic operations"""
    
    def test_qdrant_server_is_running(self):
        """✅ Test Case 1: Qdrant server is accessible"""
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        client = QdrantClient(url=qdrant_url)
        
        # Test connection by getting collections
        collections = client.get_collections()
        assert collections is not None
        print(f"✅ Qdrant server is running at {qdrant_url}")
        print(f"📊 Collections: {[col.name for col in collections.collections]}")
    
    def test_qdrant_collection_creation(self):
        """✅ Test Case 2: Can create Qdrant collection"""
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        client = QdrantClient(url=qdrant_url)
        
        test_collection = "test_collection_temp"
        
        # Clean up if exists
        try:
            client.delete_collection(test_collection)
        except:
            pass
        
        # Create collection
        client.create_collection(
            collection_name=test_collection,
            vectors_config=VectorParams(
                size=768,
                distance=Distance.COSINE
            )
        )
        
        # Verify creation
        collections = client.get_collections()
        collection_names = [col.name for col in collections.collections]
        assert test_collection in collection_names
        
        # Clean up
        client.delete_collection(test_collection)
        print(f"✅ Successfully created and deleted test collection")


class TestQdrantVectorStore:
    """Test QdrantVectorStore operations"""
    
    @pytest.fixture
    def qdrant_store(self):
        """Create a fresh Qdrant vector store for testing"""
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        collection_name = "test_pdf_chunks"
        
        # Create store
        store = QdrantVectorStore(
            collection_name=collection_name,
            qdrant_url=qdrant_url
        )
        
        # Clean up any existing data
        try:
            store._client.delete_collection(collection_name)
            store._initialize_collection()
        except:
            pass
        
        yield store
        
        # Cleanup after test
        try:
            store._client.delete_collection(collection_name)
        except:
            pass
    
    def test_add_chunks_to_qdrant(self, qdrant_store: QdrantVectorStore):
        """✅ Test Case 3: Add chunks to Qdrant"""
        initial_size = qdrant_store.size
        
        chunks = [
            Chunk(
                id="chunk1",
                content="Machine learning is a subset of artificial intelligence.",
                metadata=ChunkMetadata(
                    chunk_id="chunk1",
                    document_id="doc1",
                    page_number=1,
                    document_heading="Introduction to ML",
                    paragraph_heading="What is ML?"
                )
            ),
            Chunk(
                id="chunk2",
                content="Python is a popular programming language for data science.",
                metadata=ChunkMetadata(
                    chunk_id="chunk2",
                    document_id="doc1",
                    page_number=2,
                    document_heading="Programming Languages",
                    paragraph_heading="Python Overview"
                )
            )
        ]
        
        qdrant_store.add_chunks(chunks)
        
        assert qdrant_store.size == initial_size + 2
        print(f"✅ Added {len(chunks)} chunks to Qdrant")
        print(f"📊 Total chunks: {qdrant_store.size}")
    
    def test_search_returns_relevant_results(self, qdrant_store: QdrantVectorStore):
        """✅ Test Case 4: Search returns relevant chunks"""
        chunks = [
            Chunk(
                id="chunk3",
                content="Deep learning uses neural networks with multiple layers.",
                metadata=ChunkMetadata(
                    chunk_id="chunk3",
                    document_id="doc2",
                    page_number=1,
                    document_heading="Deep Learning",
                    paragraph_heading="Neural Networks"
                )
            ),
            Chunk(
                id="chunk4",
                content="Natural language processing helps computers understand human language.",
                metadata=ChunkMetadata(
                    chunk_id="chunk4",
                    document_id="doc2",
                    page_number=2,
                    document_heading="NLP",
                    paragraph_heading="Language Understanding"
                )
            )
        ]
        
        qdrant_store.add_chunks(chunks)
        
        # Search for relevant content
        results = qdrant_store.search("What is deep learning?", top_k=5)
        
        assert len(results) > 0
        assert all(isinstance(chunk, Chunk) for chunk, _ in results)
        assert all(isinstance(score, float) for _, score in results)
        assert all(0 <= score <= 1 for _, score in results)
        
        print(f"✅ Search returned {len(results)} results")
        for i, (chunk, score) in enumerate(results, 1):
            print(f"   {i}. Page {chunk.metadata.page_number} - Score: {score:.4f}")
    
    def test_search_respects_top_k(self, qdrant_store: QdrantVectorStore):
        """✅ Test Case 5: Search respects top_k parameter"""
        chunks = [
            Chunk(
                id=f"chunk{i}",
                content=f"Content about artificial intelligence topic {i}",
                metadata=ChunkMetadata(
                    chunk_id=f"chunk{i}",
                    document_id="doc3",
                    page_number=i,
                    document_heading=f"Section {i}",
                    paragraph_heading=f"Topic {i}"
                )
            )
            for i in range(10)
        ]
        
        qdrant_store.add_chunks(chunks)
        
        results = qdrant_store.search("artificial intelligence", top_k=3)
        
        assert len(results) <= 3
        print(f"✅ Top-k parameter respected: {len(results)} results")
    
    def test_search_filters_by_document_id(self, qdrant_store: QdrantVectorStore):
        """✅ Test Case 6: Search can filter by document_ids"""
        chunks = [
            Chunk(
                id="chunk_doc1",
                content="Content from document 1 about machine learning",
                metadata=ChunkMetadata(
                    chunk_id="chunk_doc1",
                    document_id="doc_filter_1",
                    page_number=1,
                    document_heading="Doc 1",
                    paragraph_heading="ML"
                )
            ),
            Chunk(
                id="chunk_doc2",
                content="Content from document 2 about machine learning",
                metadata=ChunkMetadata(
                    chunk_id="chunk_doc2",
                    document_id="doc_filter_2",
                    page_number=1,
                    document_heading="Doc 2",
                    paragraph_heading="ML"
                )
            )
        ]
        
        qdrant_store.add_chunks(chunks)
        
        # Search with document filter
        results = qdrant_store.search(
            "machine learning",
            top_k=10,
            document_ids={"doc_filter_1"}
        )
        
        assert len(results) > 0
        assert all(chunk.metadata.document_id == "doc_filter_1" for chunk, _ in results)
        print(f"✅ Document filtering works: {len(results)} results from doc_filter_1")
    
    def test_delete_chunks_by_document(self, qdrant_store: QdrantVectorStore):
        """✅ Test Case 7: Can delete chunks by document_id"""
        chunks = [
            Chunk(
                id=f"chunk_del_{i}",
                content=f"Content to be deleted {i}",
                metadata=ChunkMetadata(
                    chunk_id=f"chunk_del_{i}",
                    document_id="doc_to_delete",
                    page_number=i,
                    document_heading="Delete Test",
                    paragraph_heading=f"Section {i}"
                )
            )
            for i in range(5)
        ]
        
        qdrant_store.add_chunks(chunks)
        initial_size = qdrant_store.size
        
        # Delete chunks
        deleted_count = qdrant_store.delete_chunks_by_document("doc_to_delete")
        
        assert deleted_count == 5
        assert qdrant_store.size == initial_size - 5
        print(f"✅ Deleted {deleted_count} chunks")
        print(f"📊 Remaining chunks: {qdrant_store.size}")
    
    def test_has_document_check(self, qdrant_store: QdrantVectorStore):
        """✅ Test Case 8: Can check if document exists"""
        chunks = [
            Chunk(
                id="chunk_exists",
                content="Test content for existence check",
                metadata=ChunkMetadata(
                    chunk_id="chunk_exists",
                    document_id="doc_exists",
                    page_number=1,
                    document_heading="Exists Test",
                    paragraph_heading="Test"
                )
            )
        ]
        
        qdrant_store.add_chunks(chunks)
        
        assert qdrant_store.has_document("doc_exists") == True
        assert qdrant_store.has_document("doc_not_exists") == False
        print(f"✅ Document existence check works")
    
    def test_similarity_threshold_filtering(self, qdrant_store: QdrantVectorStore):
        """✅ Test Case 9: Search respects similarity threshold"""
        chunks = [
            Chunk(
                id="chunk_threshold",
                content="Quantum computing uses quantum mechanics principles",
                metadata=ChunkMetadata(
                    chunk_id="chunk_threshold",
                    document_id="doc_threshold",
                    page_number=1,
                    document_heading="Quantum",
                    paragraph_heading="Computing"
                )
            )
        ]
        
        qdrant_store.add_chunks(chunks)
        
        # Search with high threshold
        results_high = qdrant_store.search(
            "quantum computing",
            similarity_threshold=0.7
        )
        
        # Search with low threshold
        results_low = qdrant_store.search(
            "quantum computing",
            similarity_threshold=0.1
        )
        
        # All results should meet threshold
        for _, score in results_high:
            assert score >= 0.7
        
        print(f"✅ Threshold filtering works")
        print(f"   High threshold (0.7): {len(results_high)} results")
        print(f"   Low threshold (0.1): {len(results_low)} results")
    
    def test_empty_store_search(self, qdrant_store: QdrantVectorStore):
        """✅ Test Case 10: Search on empty store returns empty list"""
        results = qdrant_store.search("any query")
        
        assert results == []
        print(f"✅ Empty store returns empty results")


class TestQdrantPersistence:
    """Test Qdrant data persistence"""
    
    def test_data_persists_across_reconnections(self):
        """✅ Test Case 11: Data persists when reconnecting to Qdrant"""
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        collection_name = "test_persistence"
        
        # Create first store and add data
        store1 = QdrantVectorStore(
            collection_name=collection_name,
            qdrant_url=qdrant_url
        )
        
        chunks = [
            Chunk(
                id="persist_chunk",
                content="This data should persist",
                metadata=ChunkMetadata(
                    chunk_id="persist_chunk",
                    document_id="persist_doc",
                    page_number=1,
                    document_heading="Persistence",
                    paragraph_heading="Test"
                )
            )
        ]
        
        store1.add_chunks(chunks)
        initial_size = store1.size
        
        # Create new store instance (simulating reconnection)
        store2 = QdrantVectorStore(
            collection_name=collection_name,
            qdrant_url=qdrant_url
        )
        
        assert store2.size == initial_size
        assert store2.has_document("persist_doc") == True
        
        # Cleanup
        store2._client.delete_collection(collection_name)
        
        print(f"✅ Data persists across reconnections")
        print(f"📊 Persisted chunks: {store2.size}")


def run_all_tests():
    """Run all Qdrant tests and print summary"""
    print("\n" + "="*80)
    print("🧪 QDRANT INTEGRATION TEST SUITE")
    print("="*80 + "\n")
    
    # Run pytest
    pytest.main([__file__, "-v", "-s"])


if __name__ == "__main__":
    run_all_tests()
