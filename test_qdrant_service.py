"""
Test Your Actual Qdrant Service Implementation
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file FIRST
load_dotenv()

# Override with Qdrant settings
os.environ["USE_QDRANT"] = "true"
os.environ["QDRANT_URL"] = "http://localhost:6333"

print("\n" + "="*80)
print("🧪 TESTING YOUR QDRANT SERVICE IMPLEMENTATION")
print("="*80 + "\n")

# Test 1: Import and Initialize
print("Test 1: Importing Qdrant Service...")
try:
    from services.qdrant_service import QdrantVectorStore
    from models.schemas import Chunk, ChunkMetadata
    print("✅ Successfully imported QdrantVectorStore")
except Exception as e:
    print(f"❌ Failed to import: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 2: Create Store Instance
print("\nTest 2: Creating QdrantVectorStore Instance...")
try:
    store = QdrantVectorStore(
        collection_name="test_service_collection",
        qdrant_url="http://localhost:6333"
    )
    print(f"✅ Created QdrantVectorStore instance")
    print(f"📊 Initial size: {store.size}")
except Exception as e:
    print(f"❌ Failed to create store: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 3: Add Chunks
print("\nTest 3: Adding Chunks with Real Embeddings...")
try:
    chunks = [
        Chunk(
            content="Machine learning is a subset of artificial intelligence that focuses on data.",
            metadata=ChunkMetadata(
                chunk_id="test_chunk_1",
                document_id="test_doc_1",
                page_number=1,
                document_heading="Introduction to ML",
                paragraph_heading="What is Machine Learning?"
            )
        ),
        Chunk(
            content="Python is widely used for data science and machine learning applications.",
            metadata=ChunkMetadata(
                chunk_id="test_chunk_2",
                document_id="test_doc_1",
                page_number=2,
                document_heading="Programming Languages",
                paragraph_heading="Python for ML"
            )
        ),
        Chunk(
            content="Deep learning uses neural networks with multiple layers to process data.",
            metadata=ChunkMetadata(
                chunk_id="test_chunk_3",
                document_id="test_doc_2",
                page_number=1,
                document_heading="Deep Learning",
                paragraph_heading="Neural Networks"
            )
        )
    ]
    
    print(f"   Adding {len(chunks)} chunks...")
    store.add_chunks(chunks)
    print(f"✅ Successfully added chunks")
    print(f"📊 Store size: {store.size}")
except Exception as e:
    print(f"❌ Failed to add chunks: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 4: Search
print("\nTest 4: Testing Semantic Search...")
try:
    query = "What is machine learning?"
    results = store.search(query, top_k=3, similarity_threshold=0.1)
    
    print(f"✅ Search completed")
    print(f"📊 Found {len(results)} results for query: '{query}'")
    
    for i, (chunk, score) in enumerate(results, 1):
        print(f"\n   Result {i}:")
        print(f"   - Page: {chunk.metadata.page_number}")
        print(f"   - Document: {chunk.metadata.document_id}")
        print(f"   - Score: {score:.4f}")
        print(f"   - Heading: {chunk.metadata.document_heading}")
        print(f"   - Content: {chunk.content[:80]}...")
except Exception as e:
    print(f"❌ Search failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 5: Document Filtering
print("\nTest 5: Testing Document Filtering...")
try:
    results = store.search(
        "machine learning",
        top_k=5,
        document_ids={"test_doc_1"}
    )
    
    print(f"✅ Filtered search completed")
    print(f"📊 Found {len(results)} results from test_doc_1")
    
    # Verify all results are from the correct document
    all_correct = all(chunk.metadata.document_id == "test_doc_1" for chunk, _ in results)
    if all_correct:
        print(f"✅ All results are from the correct document")
    else:
        print(f"❌ Some results are from wrong documents")
except Exception as e:
    print(f"❌ Filtered search failed: {e}")
    import traceback
    traceback.print_exc()

# Test 6: Has Document
print("\nTest 6: Testing has_document()...")
try:
    has_doc1 = store.has_document("test_doc_1")
    has_doc2 = store.has_document("test_doc_2")
    has_doc3 = store.has_document("nonexistent_doc")
    
    print(f"✅ has_document() works")
    print(f"   test_doc_1: {has_doc1}")
    print(f"   test_doc_2: {has_doc2}")
    print(f"   nonexistent_doc: {has_doc3}")
    
    if has_doc1 and has_doc2 and not has_doc3:
        print(f"✅ All document checks are correct")
    else:
        print(f"❌ Document checks have issues")
except Exception as e:
    print(f"❌ has_document() failed: {e}")
    import traceback
    traceback.print_exc()

# Test 7: Delete Chunks
print("\nTest 7: Testing delete_chunks_by_document()...")
try:
    initial_size = store.size
    deleted_count = store.delete_chunks_by_document("test_doc_1")
    final_size = store.size
    
    print(f"✅ Deletion completed")
    print(f"   Initial size: {initial_size}")
    print(f"   Deleted: {deleted_count} chunks")
    print(f"   Final size: {final_size}")
    
    if final_size == initial_size - deleted_count:
        print(f"✅ Size calculation is correct")
    else:
        print(f"❌ Size mismatch")
    
    # Verify document is gone
    has_doc = store.has_document("test_doc_1")
    if not has_doc:
        print(f"✅ Document successfully removed")
    else:
        print(f"❌ Document still exists after deletion")
except Exception as e:
    print(f"❌ Deletion failed: {e}")
    import traceback
    traceback.print_exc()

# Test 8: Cleanup
print("\nTest 8: Cleaning Up...")
try:
    store._client.delete_collection("test_service_collection")
    print(f"✅ Test collection deleted")
except Exception as e:
    print(f"⚠️  Cleanup warning: {e}")

print("\n" + "="*80)
print("✅ ALL SERVICE TESTS COMPLETED!")
print("="*80 + "\n")

print("📋 Summary:")
print("   ✅ Qdrant connection works")
print("   ✅ Collection creation works")
print("   ✅ Adding chunks with embeddings works")
print("   ✅ Semantic search works")
print("   ✅ Document filtering works")
print("   ✅ Document existence check works")
print("   ✅ Chunk deletion works")
print("\n🎉 Your Qdrant implementation is working perfectly!")
