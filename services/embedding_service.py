import os
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()


class EmbeddingService:
    """Google Gemini-based embedding service with dynamic dimension detection"""
   
    KNOWN_DIMENSIONS: dict[str, int] = {
        "models/gemini-embedding-001": 3072,
        "models/gemini-embedding-2-preview": 768,
    }

    def __init__(self):
        """Initialize Google Gemini embedding service with API key and detect model dimensions"""
        google_api_key = os.getenv("GOOGLE_API_KEY")
        
        if not google_api_key:
            raise ValueError(
                "❌ GOOGLE_API_KEY is required for embeddings. "
                "Please set GOOGLE_API_KEY in your .env file."
            )
        
        genai.configure(api_key=google_api_key)
        self.model_name = os.getenv("EMBEDDING_MODEL_NAME", "models/gemini-embedding-001")
        
        # Dynamically detect embedding dimensions
        self._dimension = self._detect_dimension()
        
        print(f"✅ Initialized Google Gemini embedding model: {self.model_name}")
        print(f"📊 Embedding dimensions: {self._dimension}")
    
    def _detect_dimension(self) -> int:
        """Detect embedding dimension by checking known models or probing API with test query"""
        # First check known dimensions
        if self.model_name in self.KNOWN_DIMENSIONS:
            return self.KNOWN_DIMENSIONS[self.model_name]
        
        # Otherwise, probe the API
        try:
            print(f"🔍 Detecting embedding dimensions for {self.model_name}...")
            result = genai.embed_content(
                model=self.model_name,
                content="dimension probe",
                task_type="retrieval_document"
            )
            dimension = len(result['embedding'])
            print(f"✅ Detected {dimension} dimensions")
            return dimension
        except Exception as e:
            raise RuntimeError(
                f"❌ Failed to detect embedding dimensions for {self.model_name}: {e}"
            ) from e
    
    def embed_text(self, text: str) -> np.ndarray:
        """Generate normalized embedding vector for a single text using Gemini API"""
        try:
            result = genai.embed_content(
                model=self.model_name,
                content=text,
                task_type="retrieval_document"
            )
            embedding = np.array(result['embedding'], dtype="float32")
            return embedding
        except Exception as e:
            raise RuntimeError(f"❌ Gemini embedding failed: {e}") from e
    
    def embed_texts(self, texts: list[str]) -> list[np.ndarray]:
        """Generate embeddings for multiple texts in parallel using ThreadPoolExecutor for performance"""
        total = len(texts)
        if total == 0:
            return []

        embeddings: list[np.ndarray] = [None] * total
        max_workers = min(4, total)

        def _embed_indexed(index: int, text: str) -> tuple[int, np.ndarray]:
            result = genai.embed_content(
                model=self.model_name,
                content=text,
                task_type="retrieval_document"
            )
            embedding = np.array(result['embedding'], dtype="float32")
            return index, embedding

        print(f"⏳ Processing {total} embeddings with Gemini ({max_workers} workers)...")

        completed = 0
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_index = {
                executor.submit(_embed_indexed, i, text): i
                for i, text in enumerate(texts)
            }

            for future in as_completed(future_to_index):
                try:
                    index, embedding = future.result()
                    embeddings[index] = embedding
                    completed += 1
                    if completed % 10 == 0 or completed == total:
                        progress = (completed / total) * 100
                        print(f"   Progress: {completed}/{total} ({progress:.1f}%)")
                except Exception as e:
                    raise RuntimeError(f"❌ Embedding failed for chunk: {e}") from e

        return embeddings
    
    @property
    def dimension(self) -> int:
        """Return embedding dimension for the active model (e.g., 768 or 3072)"""
        return self._dimension


# Global instance
embedding_service = EmbeddingService()
