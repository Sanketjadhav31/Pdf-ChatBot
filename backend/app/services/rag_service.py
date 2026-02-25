from __future__ import annotations

import math
import uuid
from typing import Dict, List, Tuple

import numpy as np

from ..models.schemas import ChatRequest, ChatResponse, Chunk, Reference


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
        for chunk in chunks:
            self._chunks.append(chunk)
            self._embeddings.append(self.embed_text(chunk.content))

    def embed_text(self, text: str) -> np.ndarray:
        # Placeholder: deterministic pseudo-random based on text hash.
        rng = np.random.default_rng(abs(hash(text)) % (2**32))
        return rng.normal(size=768).astype("float32")

    def search(
        self,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.3,
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

        top_indices = np.argsort(-cosine_sim)[:top_k]

        results: List[Tuple[Chunk, float]] = []
        for idx in top_indices:
            score = float(cosine_sim[idx])
            if score < similarity_threshold:
                continue
            results.append((self._chunks[int(idx)], score))

        return results


class ChatOrchestrator:
    """
    High-level orchestration for chat, applying basic guardrails.
    """

    def __init__(self, store: InMemoryVectorStore) -> None:
        self._store = store
        self._sessions: Dict[str, List[str]] = {}

    def handle_chat(self, request: ChatRequest) -> ChatResponse:
        session_id = request.session_id or str(uuid.uuid4())
        history = self._sessions.setdefault(session_id, [])
        history.append(request.question)

        # Out-of-scope handling: if there are no documents yet
        if self._store.size == 0:
            return ChatResponse(
                answer=(
                    "No documents have been uploaded yet. "
                    "Please upload one or more PDFs and then ask a question based on their content."
                ),
                references=[],
                session_id=session_id,
            )

        results = self._store.search(request.question)

        if not results:
            return ChatResponse(
                answer=(
                    "This question is not related to the uploaded documents. "
                    "Please ask a question based on the document content."
                ),
                references=[],
                session_id=session_id,
            )

        # For step 1, we avoid calling a real LLM and instead
        # return a concise summary-like stub built from the top chunk.
        top_chunk, _ = results[0]

        answer = (
            "Here is a relevant excerpt from your documents:\n\n"
            f"{top_chunk.content[:800]}..."
        )

        references: List[Reference] = []
        added_keys = set()

        for chunk, _score in results:
            key = (chunk.metadata.document_id, chunk.metadata.page_number)
            if key in added_keys:
                continue
            added_keys.add(key)

            references.append(
                Reference(
                    document_id=chunk.metadata.document_id,
                    page_number=chunk.metadata.page_number,
                    document_heading=chunk.metadata.document_heading,
                    paragraph_heading=chunk.metadata.paragraph_heading,
                )
            )

        return ChatResponse(
            answer=answer,
            references=references,
            session_id=session_id,
        )


vector_store = InMemoryVectorStore()
chat_orchestrator = ChatOrchestrator(vector_store)

