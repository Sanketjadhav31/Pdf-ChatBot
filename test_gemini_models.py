#!/usr/bin/env python3
"""Test script to list available Gemini models"""
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("❌ No GOOGLE_API_KEY found")
    exit(1)

genai.configure(api_key=api_key)

print("=" * 80)
print("AVAILABLE GEMINI MODELS")
print("=" * 80)

print("\n📝 GENERATION MODELS (for chat/text generation):")
print("-" * 80)
for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"✅ {model.name}")

print("\n🔢 EMBEDDING MODELS (for vector embeddings):")
print("-" * 80)
for model in genai.list_models():
    if 'embedContent' in model.supported_generation_methods:
        print(f"✅ {model.name}")

print("\n" + "=" * 80)
print("Testing embedding model...")
print("=" * 80)

# Test the embedding
try:
    result = genai.embed_content(
        model="models/text-embedding-004",
        content="test",
        task_type="retrieval_document"
    )
    print(f"✅ models/text-embedding-004 works! Dimensions: {len(result['embedding'])}")
except Exception as e:
    print(f"❌ models/text-embedding-004 failed: {e}")

print("\n" + "=" * 80)
