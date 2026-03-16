import os
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()


class EmbeddingService:
    """Service to handle text embeddings using Google's Generative AI"""
    
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        self.client = genai.Client(api_key=api_key)
        self.model_name = "models/gemini-embedding-001"
        print(f"Initialized Google embedding model: {self.model_name}")
        print(f"Embedding dimension: 3072")
    
    def embed_text(self, text: str) -> np.ndarray:
        """Generate embedding for a single text"""
        result = self.client.models.embed_content(
            model=self.model_name,
            contents=text
        )
        embedding = np.array(result.embeddings[0].values, dtype="float32")
        return embedding
    
    def embed_texts(self, texts: list[str]) -> list[np.ndarray]:
        """Generate embeddings for multiple texts with progress tracking.

        Uses a small thread pool to parallelise requests to the Gemini
        embedding API for faster processing while keeping concurrency
        modest to avoid hammering rate limits.
        """
        total = len(texts)
        if total == 0:
            return []

        embeddings: list[np.ndarray | None] = [None] * total
        max_workers = min(4, total)

        def _embed_indexed(index: int, text: str) -> tuple[int, np.ndarray]:
            result = self.client.models.embed_content(
                model=self.model_name,
                contents=text,
            )
            embedding = np.array(result.embeddings[0].values, dtype="float32")
            return index, embedding

        print(f"⏳ Processing embeddings with {max_workers} workers...")

        completed = 0
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_index = {
                executor.submit(_embed_indexed, i, text): i
                for i, text in enumerate(texts)
            }

            for future in as_completed(future_to_index):
                index, embedding = future.result()
                embeddings[index] = embedding
                completed += 1
                if completed % 10 == 0 or completed == total:
                    progress = (completed / total) * 100
                    print(f"   Progress: {completed}/{total} ({progress:.1f}%)")

        # Strip type helper Nones (should not exist in practice)
        return [e for e in embeddings if e is not None]
    
    @property
    def dimension(self) -> int:
        """Get the embedding dimension (Google's gemini-embedding-001 is 3072)"""
        return 3072


# Global instance
embedding_service = EmbeddingService()
