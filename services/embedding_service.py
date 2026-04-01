import os
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class EmbeddingService:
   
    KNOWN_DIMENSIONS: dict[str, int] = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
    }

    def __init__(self):
        # Try Google API key first, but we'll use OpenAI for embeddings
        google_api_key = os.getenv("GOOGLE_API_KEY")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not openai_api_key:
            # If no OpenAI key, create a dummy one and use Google Gemini for generation only
            # For embeddings, we'll use a simple fallback
            print("⚠️ No OPENAI_API_KEY found. Using fallback embedding method.")
            self.client = None
            self.model_name = "fallback"
            self._dimension = 768
        else:
            self.client = OpenAI(api_key=openai_api_key)
            self.model_name = os.getenv("EMBEDDING_MODEL_NAME", "text-embedding-3-small")
            self._dimension = None
            print(f"Initialized OpenAI embedding model: {self.model_name}")
            self._dimension = self._resolve_dimension()
            print(f"Embedding dimensions: {self._dimension}")
    
    def _create_fallback_embedding(self, text: str) -> np.ndarray:
        """Create a simple hash-based embedding as fallback"""
        import hashlib
        # Create a deterministic embedding from text hash
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()
        # Expand to 768 dimensions
        embedding = np.frombuffer(hash_bytes * 24, dtype=np.uint8)[:768].astype(np.float32)
        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        return embedding
    
    def embed_text(self, text: str) -> np.ndarray:
        """Generate embedding for a single text"""
        if self.client is None:
            return self._create_fallback_embedding(text)
            
        response = self.client.embeddings.create(
            model=self.model_name,
            input=text
        )
        embedding = np.array(response.data[0].embedding, dtype="float32")
        return embedding
    
    def embed_texts(self, texts: list[str]) -> list[np.ndarray]:
        """Generate embeddings for multiple texts with progress tracking."""
        total = len(texts)
        if total == 0:
            return []

        if self.client is None:
            # Use fallback for all texts
            print(f"⏳ Using fallback embedding method for {total} texts...")
            embeddings = []
            for i, text in enumerate(texts):
                embeddings.append(self._create_fallback_embedding(text))
                if (i + 1) % 10 == 0 or (i + 1) == total:
                    progress = ((i + 1) / total) * 100
                    print(f"   Progress: {i + 1}/{total} ({progress:.1f}%)")
            return embeddings

        embeddings: list[np.ndarray | None] = [None] * total
        max_workers = min(4, total)

        def _embed_indexed(index: int, text: str) -> tuple[int, np.ndarray]:
            response = self.client.embeddings.create(
                model=self.model_name,
                input=text
            )
            embedding = np.array(response.data[0].embedding, dtype="float32")
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

        return [e for e in embeddings if e is not None]
    
    @property
    def dimension(self) -> int:
        """Get the embedding dimension for the active model."""
        if self._dimension is None:
            self._dimension = self._resolve_dimension()
        return self._dimension

    def _resolve_dimension(self) -> int:
        """Resolve model dimension from probe with safe fallback to known registry."""
        if self.client is None:
            return 768
            
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
        if self.client is None:
            return 768
            
        response = self.client.embeddings.create(
            model=self.model_name,
            input="dimension_probe"
        )
        return len(response.data[0].embedding)


# Global instance
embedding_service = EmbeddingService()
