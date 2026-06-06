from datetime import datetime
from uuid import UUID, uuid4
from beanie import Document
from pydantic import Field
from typing import Optional
from pymongo import IndexModel, ASCENDING

class EmbeddingJobDocument(Document):
    id: UUID = Field(default_factory=uuid4, alias="_id")
    profile_id: UUID
    status: str  # PENDING, PROCESSING, COMPLETED, FAILED
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "embedding_jobs"
        use_revision = False
        indexes = [
            IndexModel([("profile_id", ASCENDING)])
        ]
