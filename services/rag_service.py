from __future__ import annotations

import math
import os
import pickle
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import faiss
import numpy as np
from dotenv import load_dotenv

from models.schemas import ChatRequest, Chunk, Reference
from services.embedding_service import embedding_service
from services.llm_service import llm_service
from logger_config import setup_logger, PerformanceTimer, log_step

load_dotenv()
logger = setup_logger(__name__)


class FAISSVectorStore:
    """FAISS-based vector store with disk persistence"""
    
    def __init__(self, persist_directory: str = "vector_store_data") -> None:
        """Initialize FAISS vector store with disk persistence for embeddings and chunks"""
        self._chunks: List[Chunk] = []
        self._persist_dir = Path(persist_directory)
        self._persist_dir.mkdir(exist_ok=True)
        
        self._index_path = self._persist_dir / "faiss.index"
        self._chunks_path = self._persist_dir / "chunks.pkl"
        
        # Initialize FAISS index
        dimension = embedding_service.dimension
        self._index = faiss.IndexFlatIP(dimension)  # Inner Product (cosine similarity)
        
        # Load existing data if available
        self._load_from_disk()

    @property
    def size(self) -> int:
        return len(self._chunks)

    def _load_from_disk(self) -> None:
        """Load FAISS index and chunks from disk on startup for persistence"""
        try:
            if self._index_path.exists() and self._chunks_path.exists():
                logger.info(f"📂 Loading vector store from disk: {self._persist_dir}")
                
                # Load FAISS index
                self._index = faiss.read_index(str(self._index_path))
                
                # Load chunks
                with open(self._chunks_path, 'rb') as f:
                    self._chunks = pickle.load(f)
                
                logger.info(f"✅ Loaded {len(self._chunks)} chunks from disk")
                logger.info(f"📊 FAISS index size: {self._index.ntotal} vectors")
            else:
                logger.info("📂 No existing vector store found, starting fresh")
        except Exception as e:
            logger.error(f"❌ Failed to load vector store from disk: {e}")
            logger.info("🔄 Starting with empty vector store")
            # Reset to empty state
            dimension = embedding_service.dimension
            self._index = faiss.IndexFlatIP(dimension)
            self._chunks = []

    def _save_to_disk(self) -> None:
        """Persist FAISS index and chunks to disk after modifications"""
        try:
            logger.info(f"💾 Saving vector store to disk: {self._persist_dir}")
            
            # Save FAISS index
            faiss.write_index(self._index, str(self._index_path))
            
            # Save chunks
            with open(self._chunks_path, 'wb') as f:
                pickle.dump(self._chunks, f)
            
            logger.info(f"✅ Saved {len(self._chunks)} chunks to disk")
        except Exception as e:
            logger.error(f"❌ Failed to save vector store to disk: {e}")

    def add_chunks(self, chunks: List[Chunk]) -> None:
        """Batch embed chunks, add to FAISS index, and persist to disk"""
        if not chunks:
            return

        # Extract all text content
        texts = [chunk.content for chunk in chunks]

        # Batch embed all texts at once
        print(f"\n{'='*60}")
        print(f"📊 EMBEDDING PROGRESS")
        print(f"{'='*60}")
        print(f"Total chunks to embed: {len(texts)}")
        print(f"Starting batch embedding...")

        embeddings = embedding_service.embed_texts(texts)

        # Normalize embeddings for cosine similarity (required for IndexFlatIP)
        embeddings_array = np.array(embeddings, dtype=np.float32)
        faiss.normalize_L2(embeddings_array)

        # Add to FAISS index
        self._index.add(embeddings_array)
        
        # Add chunks to list
        self._chunks.extend(chunks)

        print(f"✅ Successfully embedded {len(chunks)} chunks")
        print(f"📚 Total chunks in vector store: {self.size}")
        print(f"{'='*60}\n")

        # Persist to disk
        self._save_to_disk()

    def has_document(self, document_id: str) -> bool:
        """Check if document has any chunks in vector store for processing status"""
        for chunk in self._chunks:
            if chunk.metadata.document_id == document_id:
                return True
        return False

    def delete_chunks_by_document(self, document_id: str) -> int:
        """Remove all chunks for a document and rebuild FAISS index (FAISS doesn't support deletion)"""
        indices_to_keep = []
        indices_to_delete = []
        deleted_count = 0

        for i, chunk in enumerate(self._chunks):
            if chunk.metadata.document_id == document_id:
                deleted_count += 1
                indices_to_delete.append(i)
            else:
                indices_to_keep.append(i)

        if deleted_count == 0:
            return 0

        # Rebuild the chunks list
        self._chunks = [self._chunks[i] for i in indices_to_keep]

        # Rebuild FAISS index (FAISS doesn't support deletion, so we rebuild)
        dimension = embedding_service.dimension
        self._index = faiss.IndexFlatIP(dimension)
        
        if self._chunks:
            # Re-embed remaining chunks
            texts = [chunk.content for chunk in self._chunks]
            embeddings = embedding_service.embed_texts(texts)
            embeddings_array = np.array(embeddings, dtype=np.float32)
            faiss.normalize_L2(embeddings_array)
            self._index.add(embeddings_array)

        print(f"🗑️  Deleted {deleted_count} chunks for document {document_id}")
        print(f"📚 Remaining chunks in vector store: {self.size}")

        # Persist changes to disk
        self._save_to_disk()

        return deleted_count

    def embed_text(self, text: str) -> np.ndarray:
        """Generate normalized embedding for search query"""
        embedding = embedding_service.embed_text(text)
        # Normalize for cosine similarity
        embedding_array = np.array([embedding], dtype=np.float32)
        faiss.normalize_L2(embedding_array)
        return embedding_array[0]

    def search(
        self,
        query: str,
        top_k: int = 10,
        similarity_threshold: float = 0.1,
        document_ids: Optional[Set[str]] = None,
    ) -> List[Tuple[Chunk, float]]:
        """Perform semantic search using FAISS with cosine similarity and optional document filtering"""
        if not self._chunks:
            return []

        with PerformanceTimer(logger, f"Vector Search (query: '{query[:50]}...')"):
            # Embed query
            query_vec = self.embed_text(query)
            query_vec = query_vec.reshape(1, -1)

            # Search FAISS index
            # Get more results than needed for filtering
            search_k = min(top_k * 3, len(self._chunks))
            distances, indices = self._index.search(query_vec, search_k)

            results: List[Tuple[Chunk, float]] = []
            for idx, score in zip(indices[0], distances[0]):
                if idx == -1:  # FAISS returns -1 for empty slots
                    continue
                    
                score = float(score)
                if score < similarity_threshold:
                    continue
                    
                chunk = self._chunks[int(idx)]
                
                # Filter by document_ids if specified
                if document_ids is not None and chunk.metadata.document_id not in document_ids:
                    continue
                    
                results.append((chunk, score))
                
                # Stop once we have enough results
                if len(results) >= top_k:
                    break

            logger.info(f"Vector search complete: {len(results)} results (threshold={similarity_threshold})")
            if results:
                logger.debug(f"Top result: Page {results[0][0].metadata.page_number}, Score: {results[0][1]:.4f}")
        
        return results


class ChatOrchestrator:
    def __init__(self, store: FAISSVectorStore) -> None:
        """Initialize chat orchestrator with vector store for RAG pipeline"""
        self._store = store
        self._sessions: Dict[str, List[str]] = {}

    def handle_chat(self, request: ChatRequest) -> dict:
        """Orchestrate RAG pipeline: search vector store, build context, and prepare references"""
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


# Initialize vector store based on USE_QDRANT flag
USE_QDRANT = os.getenv("USE_QDRANT", "false").lower() == "true"

if USE_QDRANT:
    logger.info("🚀 Using Qdrant vector store")
    from services.qdrant_service import QdrantVectorStore
    
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    collection_name = os.getenv("QDRANT_COLLECTION", "pdf_chunks")
    
    vector_store = QdrantVectorStore(
        collection_name=collection_name,
        qdrant_url=qdrant_url
    )
else:
    logger.info("🚀 Using FAISS vector store")
    vector_store = FAISSVectorStore(persist_directory="vector_store_data")

chat_orchestrator = ChatOrchestrator(vector_store)

