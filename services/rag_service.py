from __future__ import annotations

import math
import uuid
from typing import Dict, List, Tuple

import numpy as np

from models.schemas import ChatRequest, ChatResponse, Chunk, Reference
from services.embedding_service import embedding_service
from services.llm_service import llm_service


class InMemoryVectorStore:
    """
    Simple in-memory vector store for step 1.

    This uses random embeddings as placeholders so that the
    API and similarity flow are in place. Later you can replace
    `embed_text` with a real embedding model and back this store
    with FAISS/Chroma/Pinecone.
    """

    def __init__(self) -> None:
        self._chunks: List[Chunk] = []
        self._embeddings: List[np.ndarray] = []

    @property
    def size(self) -> int:
        return len(self._chunks)

    def add_chunks(self, chunks: List[Chunk]) -> None:
        """Add chunks with batch embedding for better performance"""
        if not chunks:
            return
        
        # Extract all text content
        texts = [chunk.content for chunk in chunks]
        
        # Batch embed all texts at once (much faster than one-by-one)
        print(f"\n{'='*60}")
        print(f"📊 EMBEDDING PROGRESS")
        print(f"{'='*60}")
        print(f"Total chunks to embed: {len(texts)}")
        print(f"Starting batch embedding...")
        
        embeddings = embedding_service.embed_texts(texts)
        
        # Add to store
        for chunk, embedding in zip(chunks, embeddings):
            self._chunks.append(chunk)
            self._embeddings.append(embedding)
        
        print(f"✅ Successfully embedded {len(chunks)} chunks")
        print(f"📚 Total chunks in vector store: {self.size}")
        print(f"{'='*60}\n")

    def embed_text(self, text: str) -> np.ndarray:
        # Use real embedding service
        return embedding_service.embed_text(text)

    def search(
        self,
        query: str,
        top_k: int = 10,
        similarity_threshold: float = 0.1,
    ) -> List[Tuple[Chunk, float]]:
        if not self._chunks:
            return []

        query_vec = self.embed_text(query)
        mat = np.stack(self._embeddings, axis=0)

        dot = mat @ query_vec
        mat_norm = np.linalg.norm(mat, axis=1)
        query_norm = float(np.linalg.norm(query_vec))

        # Avoid division by zero
        denom = mat_norm * query_norm + 1e-8
        cosine_sim = dot / denom

        # Get top_k results sorted by similarity
        top_indices = np.argsort(-cosine_sim)[:top_k]

        results: List[Tuple[Chunk, float]] = []
        for idx in top_indices:
            score = float(cosine_sim[idx])
            print(f"Debug: Chunk {idx} similarity score: {score:.4f} - Preview: {self._chunks[int(idx)].content[:100]}")
            if score < similarity_threshold:
                continue
            results.append((self._chunks[int(idx)], score))

        print(f"Debug: Query '{query}' returned {len(results)} results (threshold={similarity_threshold}) out of {len(self._chunks)} chunks")
        return results


class ChatOrchestrator:
    def __init__(self, store: InMemoryVectorStore) -> None:
        self._store = store
        self._sessions: Dict[str, List[str]] = {}

    def handle_chat(self, request: ChatRequest) -> ChatResponse:
        session_id = request.session_id or str(uuid.uuid4())
        history = self._sessions.setdefault(session_id, [])
        history.append(request.question)

        query_lower = request.question.lower().strip()
        
        # Try with a lower threshold first (0.2 instead of 0.3)
        # This helps with short queries and specific names
        results = self._store.search(request.question, similarity_threshold=0.2, top_k=10)

        if not results:
            # If no results, try with even lower threshold
            print(f"Debug: No results with threshold 0.2, trying with 0.0")
            results = self._store.search(request.question, similarity_threshold=0.0, top_k=10)
            
            if not results:
                return ChatResponse(
                    answer=(
                        "This question is not related to the uploaded documents. "
                        "Please ask a question based on the document content."
                    ),
                    references=[],
                    session_id=session_id,
                )

        # Build context from top results with page numbers
        context_parts = []
        for i, (chunk, score) in enumerate(results[:5], 1):
            page_info = f"Page {chunk.metadata.page_number}"
            context_parts.append(f"[Source {i} - {page_info}]:\n{chunk.content}")
        
        context = "\n\n".join(context_parts)

        # Generate answer using LLM (this will be async in the endpoint)
        # For now, we'll handle this in the chat endpoint
        references: List[Reference] = []
        added_keys = set()

        # Only include top chunks as references
        # Filter by similarity threshold of 0.6 (60% similarity)
        # This ensures only truly relevant pages are shown as sources
        # Adjust this value if you want more/fewer sources:
        # - Higher (0.65-0.7): Very strict, only most relevant pages
        # - Lower (0.4-0.5): More lenient, includes somewhat related pages
        REFERENCE_THRESHOLD = 0.6
        
        for chunk, score in results[:5]:
            print(f"Debug: Evaluating chunk - Page {chunk.metadata.page_number}, Score: {score:.4f}, Threshold: {REFERENCE_THRESHOLD}")
            if score < REFERENCE_THRESHOLD:
                print(f"  ❌ Skipped (score {score:.4f} < {REFERENCE_THRESHOLD})")
                continue
                
            key = (chunk.metadata.document_id, chunk.metadata.page_number)
            if key in added_keys:
                print(f"  ⚠️  Skipped (duplicate page)")
                continue
            added_keys.add(key)
            
            print(f"  ✅ Added to references")

            references.append(
                Reference(
                    document_id=chunk.metadata.document_id,
                    page_number=chunk.metadata.page_number,
                    document_heading=chunk.metadata.document_heading,
                    paragraph_heading=chunk.metadata.paragraph_heading,
                )
            )
        
        print(f"Debug: Total references returned: {len(references)}")
        print(f"Debug: Reference pages: {[ref.page_number for ref in references]}")

        return {
            "context": context,
            "references": references,
            "session_id": session_id,
        }


vector_store = InMemoryVectorStore()
chat_orchestrator = ChatOrchestrator(vector_store)

