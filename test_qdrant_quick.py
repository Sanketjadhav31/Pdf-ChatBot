"""
Quick Qdrant Test Script
Tests basic Qdrant functionality without full test framework
"""
import os
os.environ["USE_QDRANT"] = "true"
os.environ["QDRANT_URL"] = "http://localhost:6333"

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import numpy as np

print("\n" + "="*80)
print("🧪 QDRANT QUICK TEST")
print("="*80 + "\n")

# Test 1: Connection
print("Test 1: Testing Qdrant Connection...")
try:
    client = QdrantClient(url="http://localhost:6333")
    collections = client.get_collections()
    print(f"✅ Connected to Qdrant successfully")
    print(f"📊 Existing collections: {[col.name for col in collections.collections]}")
except Exception as e:
    print(f"❌ Failed to connect: {e}")
    exit(1)

# Test 2: Create Collection
print("\nTest 2: Creating Test Collection...")
test_collection = "quick_test_collection"
try:
    # Delete if exists
    try:
        client.delete_collection(test_collection)
    except:
        pass
    
    client.create_collection(
        collection_name=test_collection,
        vectors_config=VectorParams(size=128, distance=Distance.COSINE)
    )
    print(f"✅ Created collection: {test_collection}")
except Exception as e:
    print(f"❌ Failed to create collection: {e}")
    exit(1)

# Test 3: Add Points
print("\nTest 3: Adding Test Data...")
try:
    points = [
        PointStruct(
            id=1,
            vector=np.random.rand(128).tolist(),
            payload={"text": "Machine learning is awesome", "page": 1}
        ),
        PointStruct(
            id=2,
            vector=np.random.rand(128).tolist(),
            payload={"text": "Python is a great language", "page": 2}
        ),
        PointStruct(
            id=3,
            vector=np.random.rand(128).tolist(),
            payload={"text": "Qdrant is a vector database", "page": 3}
        )
    ]
    
    client.upsert(collection_name=test_collection, points=points, wait=True)
    print(f"✅ Added {len(points)} points to collection")
except Exception as e:
    print(f"❌ Failed to add points: {e}")
    exit(1)

# Test 4: Search
print("\nTest 4: Testing Search...")
try:
    query_vector = np.random.rand(128).tolist()
    results = client.query_points(
        collection_name=test_collection,
        query=query_vector,
        limit=3
    ).points
    print(f"✅ Search returned {len(results)} results")
    for i, result in enumerate(results, 1):
        print(f"   {i}. Page {result.payload['page']} - Score: {result.score:.4f}")
        print(f"      Text: {result.payload['text']}")
except Exception as e:
    print(f"❌ Search failed: {e}")
    exit(1)

# Test 5: Get Collection Info
print("\nTest 5: Getting Collection Info...")
try:
    info = client.get_collection(test_collection)
    print(f"✅ Collection info retrieved")
    print(f"   Points count: {info.points_count}")
except Exception as e:
    print(f"❌ Failed to get collection info: {e}")
    exit(1)

# Test 6: Delete Collection
print("\nTest 6: Cleaning Up...")
try:
    client.delete_collection(test_collection)
    print(f"✅ Deleted test collection")
except Exception as e:
    print(f"❌ Failed to delete collection: {e}")

print("\n" + "="*80)
print("✅ ALL TESTS PASSED!")
print("="*80 + "\n")

print("🎉 Qdrant is working correctly!")
print("\nNext steps:")
print("1. Set USE_QDRANT=true in your .env file to use Qdrant")
print("2. Make sure Qdrant container is running: docker-compose -f docker-compose.qdrant.yml up -d")
print("3. Your application will now use Qdrant for vector storage")
