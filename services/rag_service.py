from __future__ import annotations

import math
import os
import uuid
from typing import Dict, List, Optional, Set, Tuple

import numpy as np

from models.schemas import ChatRequest, Chunk, Reference
from services.embedding_service import embedding_service
from services.llm_service import llm_service
from logger_config import setup_logger, PerformanceTimer, log_step

logger = setup_logger(__name__)


class InMemoryVectorStore:
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
        logger.info(f"Starting batch embedding for {len(texts)} chunks")
        
        with PerformanceTimer(logger, f"Batch Embedding ({len(texts)} chunks)"):
            embeddings = embedding_service.embed_texts(texts)
        
        # Add to store
        for chunk, embedding in zip(chunks, embeddings):
            self._chunks.append(chunk)
            self._embeddings.append(embedding)
        
        logger.info(f"Successfully embedded {len(chunks)} chunks")
        logger.info(f"Total chunks in vector store: {self.size}")

    def delete_chunks_by_document(self, document_id: str) -> int:
        """Delete all chunks belonging to a specific document"""
        indices_to_keep = []
        deleted_count = 0
        
        for i, chunk in enumerate(self._chunks):
            if chunk.metadata.document_id == document_id:
                deleted_count += 1
            else:
                indices_to_keep.append(i)
        
        # Rebuild the lists without the deleted chunks
        self._chunks = [self._chunks[i] for i in indices_to_keep]
        self._embeddings = [self._embeddings[i] for i in indices_to_keep]
        
        logger.info(f"Deleted {deleted_count} chunks for document {document_id}")
        logger.info(f"Remaining chunks in vector store: {self.size}")
        
        return deleted_count
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

    def delete_chunks_by_document(self, document_id: str) -> int:
        """Delete all chunks belonging to a specific document"""
        indices_to_keep = []
        deleted_count = 0

        for i, chunk in enumerate(self._chunks):
            if chunk.metadata.document_id == document_id:
                deleted_count += 1
            else:
                indices_to_keep.append(i)

        # Rebuild the lists without the deleted chunks
        self._chunks = [self._chunks[i] for i in indices_to_keep]
        self._embeddings = [self._embeddings[i] for i in indices_to_keep]

        print(f"🗑️  Deleted {deleted_count} chunks for document {document_id}")
        print(f"📚 Remaining chunks in vector store: {self.size}")

        return deleted_count

    def embed_text(self, text: str) -> np.ndarray:
        # Use real embedding service
        return embedding_service.embed_text(text)

    def search(
        self,
        query: str,
        top_k: int = 10,
        similarity_threshold: float = 0.1,
        document_ids: Optional[Set[str]] = None,
    ) -> List[Tuple[Chunk, float]]:
        if not self._chunks:
            return []

        with PerformanceTimer(logger, f"Vector Search (query: '{query[:50]}...')"):
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
                if score < similarity_threshold:
                    continue
                chunk = self._chunks[int(idx)]
                if document_ids is not None and chunk.metadata.document_id not in document_ids:
                    continue
                results.append((chunk, score))

            logger.info(f"Vector search complete: {len(results)} results (threshold={similarity_threshold})")
            if results:
                logger.debug(f"Top result: Page {results[0][0].metadata.page_number}, Score: {results[0][1]:.4f}")
        
        return results


class ChatOrchestrator:
    def __init__(self, store: InMemoryVectorStore) -> None:
        self._store = store
        self._sessions: Dict[str, List[str]] = {}

    def handle_chat(self, request: ChatRequest) -> dict:
        session_id = request.session_id or str(uuid.uuid4())
        # Note: conversation history is persisted in the DB layer (api/v1/chat.py).
        # This orchestrator only builds PDF context from the vector store.

        query_lower = request.question.lower().strip()

        # Important: if `document_ids` is provided but empty, treat it as
        # "no PDF context for this message" (even if the server has other PDFs).
        allowed_document_ids = None
        if request.document_ids is not None:
            allowed_document_ids = set(request.document_ids)

        # If the client explicitly provided an empty document_ids array,
        # it means: "no PDFs are active for this message".
        if allowed_document_ids is not None and len(allowed_document_ids) == 0:
            return {"context": "", "references": [], "session_id": session_id}

        if self._store.size == 0:
            return {"context": "", "references": [], "session_id": session_id}

        # Try with a lower threshold first (0.2 instead of 0.3)
        # This helps with short queries and specific names.
        results = self._store.search(
            request.question,
            similarity_threshold=0.2,
            top_k=10,
            document_ids=allowed_document_ids,
        )

        if not results:
            # If no results, try with even lower threshold.
            logger.warning("No results with threshold 0.2, retrying with 0.0")
            results = self._store.search(
                request.question,
                similarity_threshold=0.0,
                top_k=10,
                document_ids=allowed_document_ids,
            )

            if not results:
                # As a final fallback, treat generic prompts like
                # "summarize this PDF" or "explain key points" as a
                # request to work with the whole document, not reject it.
                summary_keywords = [
                    "summary",
                    "summarize",
                    "summrise",
                    "summarise",
                    "key points",
                    "key point",
                    "explain",
                    "overview",
                ]
                if any(k in query_lower for k in summary_keywords):
                    # Use the first few chunks as context for a high‑level
                    # summary answer.
                    logger.info("Summary request detected with no semantic matches")
                    logger.info("Using first 10 chunks for general summary")
                    base_chunks = list(getattr(self._store, "_chunks", []))
                    if allowed_document_ids is not None:
                        base_chunks = [
                            c for c in base_chunks if c.metadata.document_id in allowed_document_ids
                        ]
                    results = [(chunk, 1.0) for chunk in base_chunks[:10]]

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

        def make_sentence_snippet(text: str, min_len: int = 80, max_len: int = 180) -> str:
            """
            Level 1 snippet: take a complete first sentence when possible.
            - Aim for at least `min_len` characters before the first sentence boundary.
            - Hard cap at `max_len` if no boundary is found.
            """
            t = (text or "").strip()
            if not t:
                return ""
            if len(t) <= max_len:
                return t

            # Prefer first period after min_len, otherwise fallback to max_len.
            boundary_idx = t.find(".", min_len)
            if boundary_idx != -1:
                return t[: boundary_idx + 1]

            # Fallback: first newline or fallback to max_len.
            nl_idx = t.find("\n", min_len)
            if nl_idx != -1:
                return t[:nl_idx].rstrip()

            return t[:max_len].rstrip() + "…"

        # Only include top chunks as references
        # Filter by similarity threshold of 0.5 (50% similarity)
        # This ensures only truly relevant pages are shown as sources
        # Adjust this value if you want more/fewer sources:
        # - Higher (0.65-0.7): Very strict, only most relevant pages
        # - Lower (0.4-0.5): More lenient, includes somewhat related pages
        REFERENCE_THRESHOLD = 0.5
        
        print(f"\n{'='*80}")
        print(f"📚 REFERENCE FILTERING")
        print(f"{'='*80}")
        print(f"Threshold: {REFERENCE_THRESHOLD} (only chunks above this score become references)")
        print(f"{'-'*80}")
        
        for i, (chunk, score) in enumerate(results[:5], 1):
            page = chunk.metadata.page_number
            status = ""
            
            if score < REFERENCE_THRESHOLD:
                status = f"❌ SKIPPED - Score too low ({score:.4f} < {REFERENCE_THRESHOLD})"
                print(f"  {i}. Page {page:2d} | Score: {score:.4f} | {status}")
                continue
                
            key = (chunk.metadata.document_id, chunk.metadata.page_number)
            if key in added_keys:
                status = f"⚠️  SKIPPED - Duplicate page"
                print(f"  {i}. Page {page:2d} | Score: {score:.4f} | {status}")
                continue
            
            added_keys.add(key)
            status = f"✅ ADDED as reference"
            print(f"  {i}. Page {page:2d} | Score: {score:.4f} | {status}")

            references.append(
                Reference(
                    document_id=chunk.metadata.document_id,
                    page_number=chunk.metadata.page_number,
                    document_heading=chunk.metadata.document_heading,
                    paragraph_heading=chunk.metadata.paragraph_heading,
                    snippet=make_sentence_snippet(chunk.content, min_len=80, max_len=180),
                    snippet_hover=make_sentence_snippet(chunk.content, min_len=80, max_len=400),
                )
            )
        
        print(f"{'-'*80}")
        print(f"✅ Total references: {len(references)}")
        if references:
            print(f"📄 Pages included: {[ref.page_number for ref in references]}")
        else:
            print(f"⚠️  No references met the threshold criteria")
        print(f"{'='*80}\n")

        return {
            "context": context,
            "references": references,
            "session_id": session_id,
        }


vector_store = InMemoryVectorStore()
chat_orchestrator = ChatOrchestrator(vector_store)

