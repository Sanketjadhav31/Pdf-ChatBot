#!/usr/bin/env python3
"""Test Gemini embedding"""
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

print("=" * 80)
print("TESTING EMBEDDING MODEL")
print("=" * 80)

model_name = "models/text-embedding-004"
print(f"\n🔍 Testing: {model_name}")

try:
    result = genai.embed_content(
        model=model_name,
        content="This is a test document about machine learning",
        task_type="retrieval_document"
    )
    print(f"✅ SUCCESS!")
    print(f"📊 Dimensions: {len(result['embedding'])}")
    print(f"📝 First 5 values: {result['embedding'][:5]}")
except Exception as e:
    print(f"❌ FAILED: {e}")
    print(f"\n🔄 Trying alternative: models/gemini-embedding-001")
    try:
        result = genai.embed_content(
            model="models/gemini-embedding-001",
            content="This is a test document about machine learning",
            task_type="retrieval_document"
        )
        print(f"✅ SUCCESS with gemini-embedding-001!")
        print(f"📊 Dimensions: {len(result['embedding'])}")
        print(f"📝 First 5 values: {result['embedding'][:5]}")
        print(f"\n⚠️  UPDATE YOUR .env TO USE: models/gemini-embedding-001")
    except Exception as e2:
        print(f"❌ Also failed: {e2}")

print("\n" + "=" * 80)
