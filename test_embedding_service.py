#!/usr/bin/env python3
"""Test the embedding service"""
import sys
sys.path.insert(0, '.')

from services.embedding_service import embedding_service

print("=" * 80)
print("TESTING EMBEDDING SERVICE")
print("=" * 80)

print(f"\n✅ Model: {embedding_service.model_name}")
print(f"✅ Dimensions: {embedding_service.dimension}")

print("\n🔍 Testing single embedding...")
try:
    embedding = embedding_service.embed_text("This is a test document")
    print(f"✅ Single embedding works! Shape: {embedding.shape}")
    print(f"📝 First 5 values: {embedding[:5]}")
except Exception as e:
    print(f"❌ Failed: {e}")
    sys.exit(1)

print("\n🔍 Testing batch embeddings...")
try:
    texts = [
        "Machine learning is a subset of artificial intelligence",
        "Python is a popular programming language",
        "Data science involves statistics and programming"
    ]
    embeddings = embedding_service.embed_texts(texts)
    print(f"✅ Batch embedding works! Count: {len(embeddings)}")
    print(f"📊 Each embedding shape: {embeddings[0].shape}")
except Exception as e:
    print(f"❌ Failed: {e}")
    sys.exit(1)

print("\n" + "=" * 80)
print("✅ ALL TESTS PASSED!")
print("=" * 80)
