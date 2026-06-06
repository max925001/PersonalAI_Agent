from typing import List, Dict, Any
from loguru import logger

from app.core.config import settings
from app.application.interfaces.vector_db_port import IVectorDatabasePort

class QdrantService:
    """Service that coordinates storing and managing vector points in Qdrant."""

    def __init__(self, vector_db_port: IVectorDatabasePort):
        self.vector_db_port = vector_db_port
        self.collection_name = settings.QDRANT_COLLECTION_NAME

    async def save_chunks_to_vector_store(self, chunks: List[Dict[str, Any]], profile_id: str, vector_size: int) -> None:
        """
        Coordinates collection verification and upserts chunks into Qdrant.
        """
        logger.info(f"Syncing chunks to Qdrant collection: {self.collection_name}")
        
        # 1. Ensure collection exists with correct dimension
        await self.vector_db_port.ensure_collection(self.collection_name, vector_size)
        
        # 2. Upsert vectors
        await self.vector_db_port.upsert_chunks(self.collection_name, chunks, profile_id)
        
        logger.info(f"Successfully finished upserting points to Qdrant.")

    async def clear_profile_vectors(self, profile_id: str) -> None:
        """Removes all vectors belonging to this profile."""
        logger.info(f"Clearing vector store records for profile_id: {profile_id}")
        await self.vector_db_port.delete_by_profile_id(self.collection_name, profile_id)

    async def get_existing_vectors(self, point_ids: List[str]) -> Dict[str, List[float]]:
        """Retrieves existing vectors from collection by point IDs."""
        return await self.vector_db_port.get_vectors_by_ids(self.collection_name, point_ids)

    async def ensure_collection_ready(self, vector_size: int) -> None:
        """Ensures collection exists with appropriate dimension and schema indices."""
        await self.vector_db_port.ensure_collection(self.collection_name, vector_size)
