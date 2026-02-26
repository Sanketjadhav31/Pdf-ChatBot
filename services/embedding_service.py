import os
import numpy as np
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
        """Generate embeddings for multiple texts with progress tracking"""
        embeddings = []
        total = len(texts)
        
        # Process in batches for better progress tracking and API efficiency
        batch_size = 100  # Increased from 50 for faster processing
        for i in range(0, total, batch_size):
            batch = texts[i:i+batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total + batch_size - 1) // batch_size
            
            print(f"⏳ Processing batch {batch_num}/{total_batches} ({len(batch)} chunks)...")
            
            # Process batch items
            batch_embeddings = []
            for idx, text in enumerate(batch):
                result = self.client.models.embed_content(
                    model=self.model_name,
                    contents=text
                )
                embedding = np.array(result.embeddings[0].values, dtype="float32")
                batch_embeddings.append(embedding)
                
                # Show progress less frequently for faster processing
                if (idx + 1) % 25 == 0 or (idx + 1) == len(batch):
                    current = i + idx + 1
                    progress = (current / total) * 100
                    print(f"   Progress: {current}/{total} ({progress:.1f}%)")
            
            embeddings.extend(batch_embeddings)
        
        return embeddings
    
    @property
    def dimension(self) -> int:
        """Get the embedding dimension (Google's gemini-embedding-001 is 3072)"""
        return 3072


# Global instance
embedding_service = EmbeddingService()
