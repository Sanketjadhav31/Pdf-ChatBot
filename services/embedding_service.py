import os
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from google import genai
from dotenv import load_dotenv

load_dotenv()


class EmbeddingService:
    """Service to handle text embeddings using Google's Generative AI"""

    KNOWN_DIMENSIONS: dict[str, int] = {
        "models/gemini-embedding-001": 3072,
        "models/text-embedding-004": 768,
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
    }

    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")

        self.client = genai.Client(api_key=api_key)
        self.model_name = os.getenv("EMBEDDING_MODEL_NAME", "models/gemini-embedding-001")
        self._dimension: int | None = None

        print(f"Initialized Google embedding model: {self.model_name}")

        # Resolve dimension once and cache it to avoid hardcoded drift.
        self._dimension = self._resolve_dimension()
        print(f"Embedding dimension: {self._dimension}")
    
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
        """Get the embedding dimension for the active model."""
        if self._dimension is None:
            self._dimension = self._resolve_dimension()
        return self._dimension

    def _resolve_dimension(self) -> int:
        """Resolve model dimension from probe with safe fallback to known registry."""
        try:
            return self._probe_dimension()
        except Exception as probe_error:
            known_dimension = self.KNOWN_DIMENSIONS.get(self.model_name)
            if known_dimension is not None:
                print(
                    f"⚠️ Dimension probe failed for {self.model_name}; "
                    f"falling back to known dimension {known_dimension}. Error: {probe_error}"
                )
                return known_dimension
            raise RuntimeError(
                f"Failed to resolve embedding dimension for model {self.model_name}: {probe_error}"
            ) from probe_error

    def _probe_dimension(self) -> int:
        """Probe embedding dimension from real API response."""
        result = self.client.models.embed_content(
            model=self.model_name,
            contents="dimension_probe",
        )
        vector = result.embeddings[0].values
        return len(vector)


# Global instance
embedding_service = EmbeddingService()
