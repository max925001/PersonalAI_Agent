import asyncio
from typing import List, Dict, Any, Optional
from loguru import logger
from app.application.interfaces.embedding_port import IEmbeddingPort
from app.application.interfaces.vector_db_port import IVectorDatabasePort
from app.core.config import settings

class RetrieverService:
    """Handles query embedding generation with local caching, and Qdrant semantic search."""

    def __init__(self, embedding_port: IEmbeddingPort, vector_db_port: IVectorDatabasePort):
        self.embedding_port = embedding_port
        self.vector_db_port = vector_db_port
        self.cache: Dict[str, List[float]] = {}
        self._lock = asyncio.Lock()

    async def get_query_embedding(self, query: str) -> List[float]:
        """Retrieves the embedding for a user query, utilizing a local memory cache."""
        query_clean = query.strip().lower()
        async with self._lock:
            if query_clean in self.cache:
                logger.info(f"Query embedding cache hit for: '{query_clean}'")
                return self.cache[query_clean]

        logger.info(f"Query embedding cache miss. Generating local embedding for: '{query_clean}'")
        embeddings = await self.embedding_port.generate_embeddings([query])
        if not embeddings:
            raise ValueError("Embedding model returned empty response for query.")
        
        query_vector = embeddings[0]
        async with self._lock:
            # Limit cache size to 1000 items to prevent memory leaks
            if len(self.cache) > 1000:
                self.cache.clear()
            self.cache[query_clean] = query_vector
            
        return query_vector

    async def retrieve_context(
        self,
        query: str,
        profile_id: Optional[str] = None,
        limit: int = 5,
        score_threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Embeds the query and searches the vector database.
        Performs duplicate chunk removal based on chunk text hash.
        """
        query_vector = await self.get_query_embedding(query)
        
        results = await self.vector_db_port.search(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            query_vector=query_vector,
            limit=limit * 2,  # Fetch slightly more to account for duplicates and thresholds
            score_threshold=score_threshold,
            profile_id=profile_id
        )
        
        # Remove duplicate chunks (deduplication) and sort by score
        seen_hashes = set()
        deduplicated = []
        
        for hit in results:
            payload = hit.get("payload", {})
            chunk_hash = payload.get("chunk_hash") or payload.get("chunk_text")
            
            if chunk_hash not in seen_hashes:
                seen_hashes.add(chunk_hash)
                deduplicated.append(hit)
                
            if len(deduplicated) >= limit:
                break
                
        return deduplicated
