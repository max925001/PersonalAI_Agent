import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from loguru import logger
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings
from app.core.exceptions import QdrantException
from app.application.interfaces.vector_db_port import IVectorDatabasePort

class QdrantAdapter(IVectorDatabasePort):
    """Qdrant client adapter implementing IVectorDatabasePort contract."""

    def __init__(self):
        # Configure client connection based on whether URL/API_KEY are provided for Qdrant Cloud
        if settings.QDRANT_URL:
            self.client = AsyncQdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY,
                timeout=settings.QDRANT_TIMEOUT
            )
            logger.info(f"Qdrant async client initialized pointing to Qdrant Cloud URL: {settings.QDRANT_URL} with timeout {settings.QDRANT_TIMEOUT}s")
        else:
            self.client = AsyncQdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT,
                timeout=settings.QDRANT_TIMEOUT
            )
            logger.info(f"Qdrant async client initialized pointing to local host {settings.QDRANT_HOST}:{settings.QDRANT_PORT} with timeout {settings.QDRANT_TIMEOUT}s")

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    async def ensure_collection(self, collection_name: str, vector_size: int) -> None:
        """Checks if collection exists, if not creates it with cosine similarity distance."""
        try:
            collections = await self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if collection_name not in collection_names:
                logger.info(f"Creating Qdrant collection '{collection_name}' (dim={vector_size})...")
                await self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
                )
                logger.info(f"Collection '{collection_name}' created successfully.")
            else:
                # Retrieve collection info to check for dimension mismatch
                info = await self.client.get_collection(collection_name)
                existing_size = None
                
                # Check single vector or named vector schema
                if hasattr(info.config.params.vectors, "size"):
                    existing_size = info.config.params.vectors.size
                elif isinstance(info.config.params.vectors, dict) and info.config.params.vectors:
                    first_val = list(info.config.params.vectors.values())[0]
                    existing_size = getattr(first_val, "size", None)
                
                if existing_size and existing_size != vector_size:
                    logger.warning(
                        f"Qdrant collection '{collection_name}' dimension mismatch! "
                        f"Existing: {existing_size}, Requested: {vector_size}. Recreating collection..."
                    )
                    await self.client.delete_collection(collection_name)
                    await self.client.create_collection(
                        collection_name=collection_name,
                        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
                    )
                    logger.info(f"Collection '{collection_name}' recreated successfully with dim={vector_size}.")
                else:
                    logger.info(f"Collection '{collection_name}' already exists and matches requested dimension ({vector_size}).")
            
            # Ensure the payload index for 'profile_id' exists (required for filtering/deletions in Qdrant)
            try:
                await self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name="profile_id",
                    field_schema="keyword"
                )
                logger.info(f"Payload index for 'profile_id' verified/created successfully in collection '{collection_name}'.")
            except Exception as index_err:
                logger.debug(f"Payload index creation note (might already exist): {str(index_err)}")
        except Exception as e:
            logger.error(f"Failed to verify or create Qdrant collection: {str(e)}")
            raise QdrantException(f"Failed to verify Qdrant collection state: {str(e)}")

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    async def upsert_chunks(self, collection_name: str, chunks: List[Dict[str, Any]], profile_id: str) -> None:
        """Deterministic bulk upsert of chunk vectors and payload schemas."""
        if not chunks:
            logger.info("No vectors to upsert to Qdrant.")
            return

        points = []
        for chunk in chunks:
            chunk_hash = chunk["hash"]
            # Generate deterministic UUID v5 from namespace DNS and chunk hash
            # This guarantees that if the same chunk content is synced again, it overwrites the exact point
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk_hash))
            
            payload = {
                "profile_id": str(profile_id),
                "source_type": chunk["metadata"]["source_type"],
                "source_id": str(chunk["metadata"]["source_id"]),
                "repository_name": chunk["metadata"].get("repository_name") or "",
                "content_hash": chunk["metadata"].get("content_hash") or "",
                "chunk_hash": chunk_hash,
                "chunk_text": chunk["text"],
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            points.append(PointStruct(
                id=point_id,
                vector=chunk["vector"],
                payload=payload
            ))

        try:
            logger.info(f"Upserting {len(points)} vectors into Qdrant collection '{collection_name}'...")
            await self.client.upsert(
                collection_name=collection_name,
                points=points
            )
            logger.info(f"Upserted {len(points)} vectors successfully.")
        except Exception as e:
            logger.exception("Qdrant points upsert failed")
            raise QdrantException(f"Failed to upsert points in vector store: {repr(e)}")

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    async def delete_by_profile_id(self, collection_name: str, profile_id: str) -> None:
        """Deletes all vector points where payload.profile_id matches the given profile ID."""
        try:
            logger.info(f"Deleting vector points in Qdrant collection '{collection_name}' for profile_id: {profile_id}")
            await self.client.delete(
                collection_name=collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="profile_id",
                            match=MatchValue(value=profile_id)
                        )
                    ]
                )
            )
            logger.info(f"Qdrant deletion complete for profile_id: {profile_id}")
        except Exception as e:
            logger.exception(f"Qdrant deletion failed for profile_id {profile_id}")
            raise QdrantException(f"Failed to delete points from vector database: {repr(e)}")

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    async def get_vectors_by_ids(self, collection_name: str, ids: List[str]) -> Dict[str, List[float]]:
        """Retrieves existing vectors from Qdrant by their point IDs."""
        if not ids:
            return {}
        try:
            # Check if collection exists first
            collections = await self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            if collection_name not in collection_names:
                return {}

            logger.info(f"Retrieving existing vectors for {len(ids)} points from Qdrant collection '{collection_name}'...")
            records = await self.client.retrieve(
                collection_name=collection_name,
                ids=ids,
                with_vectors=True,
                with_payload=False
            )
            
            # Map point ID to its vector
            vectors = {}
            for record in records:
                if record.vector:
                    if isinstance(record.vector, list):
                        vectors[str(record.id)] = record.vector
            return vectors
        except Exception as e:
            logger.warning(f"Failed to retrieve existing vectors from Qdrant: {str(e)}")
            return {}

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 5,
        score_threshold: float = 0.7,
        profile_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Performs semantic similarity search with optional filtering by profile_id and score threshold."""
        try:
            query_filter = None
            if profile_id:
                query_filter = Filter(
                    must=[
                        FieldCondition(
                            key="profile_id",
                            match=MatchValue(value=str(profile_id))
                        )
                    ]
                )

            logger.info(f"Searching Qdrant collection '{collection_name}' (limit={limit}, threshold={score_threshold}, profile_id={profile_id})...")
            
            response = await self.client.query_points(
                collection_name=collection_name,
                query=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=query_filter
            )
            
            mapped_results = []
            for hit in response.points:
                mapped_results.append({
                    "id": str(hit.id),
                    "score": hit.score,
                    "payload": hit.payload
                })
            
            logger.info(f"Found {len(mapped_results)} matching points in Qdrant.")
            return mapped_results
        except Exception as e:
            logger.exception("Qdrant similarity search failed")
            raise QdrantException(f"Failed to search similarity in vector store: {repr(e)}")
