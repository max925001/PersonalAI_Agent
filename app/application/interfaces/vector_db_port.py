from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class IVectorDatabasePort(ABC):
    """Port contract for Vector Database operations (e.g. Qdrant)."""

    @abstractmethod
    async def ensure_collection(self, collection_name: str, vector_size: int) -> None:
        """Ensures that the specified collection exists with correct vector size and configuration."""
        pass

    @abstractmethod
    async def upsert_chunks(self, collection_name: str, chunks: List[Dict[str, Any]], profile_id: str) -> None:
        """
        Upserts chunk vectors and payload data into Qdrant collection.
        Ensures points are generated deterministically to avoid duplicates.
        """
        pass

    @abstractmethod
    async def delete_by_profile_id(self, collection_name: str, profile_id: str) -> None:
        """Deletes all vector points associated with a specific profile ID."""
        pass

    @abstractmethod
    async def get_vectors_by_ids(self, collection_name: str, ids: List[str]) -> Dict[str, List[float]]:
        """Retrieves existing vectors from collection by point IDs."""
        pass

    @abstractmethod
    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 5,
        score_threshold: float = 0.7,
        profile_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Performs similarity search in the vector database.
        Returns a list of matching points with payload and score.
        """
        pass
