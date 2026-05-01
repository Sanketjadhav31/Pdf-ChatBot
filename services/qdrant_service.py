from __future__ import annotations

import os
from typing import List, Optional, Set, Tuple
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue, PayloadSchemaType
import numpy as np

from models.schemas import Chunk, ChunkMetadata
from services.embedding_service import embedding_service
from logger_config import setup_logger, PerformanceTimer

logger = setup_logger(__name__)


class QdrantVectorStore:
    """Qdrant-based vector store with local Docker or Cloud persistence"""
    
    def __init__(
        self, 
        collection_name: str = "pdf_chunks",
        qdrant_url: str = "http://localhost:6333",
        api_key: Optional[str] = None
    ) -> None:
        """Initialize Qdrant vector store with connection to local Docker or Cloud instance"""
        self._collection_name = collection_name
        self._qdrant_url = qdrant_url
        self._api_key = api_key
        self._chunks: List[Chunk] = []  # Keep chunks in memory for metadata
        
        try:
            # Connect to Qdrant (with or without API key)
            if self._api_key:
                self._client = QdrantClient(url=self._qdrant_url, api_key=self._api_key)
                logger.info(f"✅ Connected to Qdrant Cloud at {self._qdrant_url}")
            else:
                self._client = QdrantClient(url=self._qdrant_url)
                logger.info(f"✅ Connected to Qdrant at {self._qdrant_url}")
            
            # Create collection if it doesn't exist
            self._initialize_collection()
            
            # Load existing chunks metadata
            self._load_chunks_metadata()
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Qdrant: {e}")
            if self._api_key:
                raise RuntimeError(
                    f"Could not connect to Qdrant Cloud at {self._qdrant_url}. "
                    "Check your QDRANT_URL and QDRANT_API_KEY environment variables."
                ) from e
            else:
                raise RuntimeError(
                    f"Could not connect to Qdrant at {self._qdrant_url}. "
                    "Make sure Qdrant Docker container is running. "
                    "Run: docker run -p 6333:6333 -p 6334:6334 "
                    "-v $(pwd)/qdrant_storage:/qdrant/storage:z qdrant/qdrant"
                ) from e

    def _initialize_collection(self) -> None:
        """Create Qdrant collection if it doesn't exist, or recreate if dimension mismatch"""
        try:
            collections = self._client.get_collections().collections
            collection_names = [col.name for col in collections]
            current_dimension = embedding_service.dimension
            
            if self._collection_name in collection_names:
                # Collection exists - check if dimension matches
                collection_info = self._client.get_collection(self._collection_name)
                existing_dimension = collection_info.config.params.vectors.size
                
                if existing_dimension != current_dimension:
                    # Dimension mismatch - delete and recreate
                    logger.warning(
                        f"⚠️  Dimension mismatch detected in collection '{self._collection_name}': "
                        f"existing={existing_dimension}, required={current_dimension}"
                    )
                    logger.info(f"🗑️  Deleting old collection with {existing_dimension} dimensions...")
                    self._client.delete_collection(self._collection_name)
                    logger.info(f"✅ Deleted old collection")
                    
                    # Create new collection with correct dimension
                    logger.info(f"🔨 Creating new collection with {current_dimension} dimensions...")
                    self._client.create_collection(
                        collection_name=self._collection_name,
                        vectors_config=VectorParams(
                            size=current_dimension,
                            distance=Distance.COSINE
                        )
                    )
                    # Create payload index for document_id filtering
                    self._client.create_payload_index(
                        collection_name=self._collection_name,
                        field_name="document_id",
                        field_schema=PayloadSchemaType.KEYWORD
                    )
                    logger.info(f"✅ Created Qdrant collection: {self._collection_name}")
                    logger.info(f"📊 Vector dimensions: {current_dimension}")
                    logger.info(f"🔍 Created payload index on 'document_id'")
                else:
                    # Dimension matches - use existing collection
                    logger.info(f"📂 Using existing Qdrant collection: {self._collection_name}")
                    logger.info(f"📊 Vector dimensions: {existing_dimension}")
                    
                    # Ensure payload index exists (for existing collections that may not have it)
                    self._ensure_payload_index()
            else:
                # Collection doesn't exist - create it
                self._client.create_collection(
                    collection_name=self._collection_name,
                    vectors_config=VectorParams(
                        size=current_dimension,
                        distance=Distance.COSINE
                    )
                )
                # Create payload index for document_id filtering
                self._client.create_payload_index(
                    collection_name=self._collection_name,
                    field_name="document_id",
                    field_schema=PayloadSchemaType.KEYWORD
                )
                logger.info(f"✅ Created Qdrant collection: {self._collection_name}")
                logger.info(f"📊 Vector dimensions: {current_dimension}")
                logger.info(f"🔍 Created payload index on 'document_id'")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize collection: {e}")
            raise

    def _ensure_payload_index(self) -> None:
        """Ensure payload index exists for document_id field (idempotent operation)"""
        try:
            # Try to create the index - Qdrant will ignore if it already exists
            self._client.create_payload_index(
                collection_name=self._collection_name,
                field_name="document_id",
                field_schema=PayloadSchemaType.KEYWORD
            )
            logger.info(f"🔍 Ensured payload index exists on 'document_id'")
        except Exception as e:
            # If index already exists, this is fine - log at debug level
            logger.debug(f"Payload index check: {e}")

    def _load_chunks_metadata(self) -> None:
        """Load chunks metadata from Qdrant on startup"""
        try:
            # Get all points from collection
            scroll_result = self._client.scroll(
                collection_name=self._collection_name,
                limit=10000,  # Adjust based on your needs
                with_payload=True,
                with_vectors=False
            )
            
            points = scroll_result[0]
            self._chunks = []
            
            for point in points:
                # Reconstruct Chunk from payload
                chunk = Chunk(
                    content=point.payload.get("content"),
                    metadata=ChunkMetadata(
                        chunk_id=point.payload.get("chunk_id"),
                        document_id=point.payload.get("document_id"),
                        page_number=point.payload.get("page_number"),
                        document_heading=point.payload.get("document_heading"),
                        paragraph_heading=point.payload.get("paragraph_heading")
                    )
                )
                self._chunks.append(chunk)
            
            logger.info(f"✅ Loaded {len(self._chunks)} chunks from Qdrant")
            
        except Exception as e:
            logger.warning(f"⚠️  Could not load chunks metadata: {e}")
            self._chunks = []

    @property
    def size(self) -> int:
        """Return total number of chunks in the vector store"""
        return len(self._chunks)

    def add_chunks(self, chunks: List[Chunk]) -> None:
        """Batch embed chunks and add to Qdrant collection"""
        if not chunks:
            return

        # Extract all text content
        texts = [chunk.content for chunk in chunks]

        print(f"\n{'='*60}")
        print(f"📊 QDRANT EMBEDDING PROGRESS")
        print(f"{'='*60}")
        print(f"Total chunks to embed: {len(texts)}")
        print(f"Starting batch embedding...")

        # Batch embed all texts
        embeddings = embedding_service.embed_texts(texts)

        # Prepare points for Qdrant
        points = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            point = PointStruct(
                id=i + len(self._chunks),  # Sequential ID
                vector=embedding.tolist(),
                payload={
                    "chunk_id": chunk.metadata.chunk_id,
                    "content": chunk.content,
                    "document_id": chunk.metadata.document_id,
                    "page_number": chunk.metadata.page_number,
                    "document_heading": chunk.metadata.document_heading,
                    "paragraph_heading": chunk.metadata.paragraph_heading
                }
            )
            points.append(point)

        # Upload to Qdrant
        self._client.upsert(
            collection_name=self._collection_name,
            wait=True,
            points=points
        )

        # Add chunks to memory
        self._chunks.extend(chunks)

        print(f"✅ Successfully embedded and stored {len(chunks)} chunks in Qdrant")
        print(f"📚 Total chunks in vector store: {self.size}")
        print(f"{'='*60}\n")

    def has_document(self, document_id: str) -> bool:
        """Check if document has any chunks in vector store"""
        for chunk in self._chunks:
            if chunk.metadata.document_id == document_id:
                return True
        return False

    def delete_chunks_by_document(self, document_id: str) -> int:
        """Remove all chunks for a document from Qdrant"""
        try:
            # Count chunks to delete
            deleted_count = sum(
                1 for chunk in self._chunks 
                if chunk.metadata.document_id == document_id
            )
            
            if deleted_count == 0:
                return 0

            # Delete from Qdrant using filter
            self._client.delete(
                collection_name=self._collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=document_id)
                        )
                    ]
                )
            )

            # Remove from memory
            self._chunks = [
                chunk for chunk in self._chunks 
                if chunk.metadata.document_id != document_id
            ]

            logger.info(f"🗑️  Deleted {deleted_count} chunks for document {document_id}")
            logger.info(f"📚 Remaining chunks in vector store: {self.size}")

            return deleted_count
            
        except Exception as e:
            logger.error(f"❌ Failed to delete chunks: {e}")
            raise

    def embed_text(self, text: str) -> np.ndarray:
        """Generate embedding for search query (for compatibility with FAISS interface)"""
        return embedding_service.embed_text(text)

    def search(
        self,
        query: str,
        top_k: int = 10,
        similarity_threshold: float = 0.1,
        document_ids: Optional[Set[str]] = None,
    ) -> List[Tuple[Chunk, float]]:
        """Perform semantic search using Qdrant with cosine similarity"""
        if not self._chunks:
            return []

        with PerformanceTimer(logger, f"Qdrant Vector Search (query: '{query[:50]}...')"):
            # Embed query
            query_embedding = embedding_service.embed_text(query)

            # Build filter if document_ids specified
            query_filter = None
            if document_ids is not None:
                query_filter = Filter(
                    should=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=doc_id)
                        )
                        for doc_id in document_ids
                    ]
                )

            # Search Qdrant
            search_results = self._client.query_points(
                collection_name=self._collection_name,
                query=query_embedding.tolist(),
                query_filter=query_filter,
                limit=top_k,
                score_threshold=similarity_threshold
            ).points

            # Convert results to expected format
            results: List[Tuple[Chunk, float]] = []
            for result in search_results:
                # Reconstruct Chunk from payload
                chunk = Chunk(
                    content=result.payload.get("content"),
                    metadata=ChunkMetadata(
                        chunk_id=result.payload.get("chunk_id"),
                        document_id=result.payload.get("document_id"),
                        page_number=result.payload.get("page_number"),
                        document_heading=result.payload.get("document_heading"),
                        paragraph_heading=result.payload.get("paragraph_heading")
                    )
                )
                results.append((chunk, result.score))

            logger.info(f"Qdrant search complete: {len(results)} results (threshold={similarity_threshold})")
            if results:
                logger.debug(f"Top result: Page {results[0][0].metadata.page_number}, Score: {results[0][1]:.4f}")
        
        return results
