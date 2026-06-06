from datetime import datetime
from uuid import UUID, uuid4
from beanie import Document
from pydantic import Field
from typing import Optional
from pymongo import IndexModel, ASCENDING

class ProcessingStatusDocument(Document):
    id: UUID = Field(default_factory=uuid4, alias="_id")
    profile_id: UUID
    current_step: str
    progress: float
    status: str  # PENDING, PROCESSING, COMPLETED, FAILED
    error_message: Optional[str] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "processing_statuses"
        use_revision = False
        indexes = [
            IndexModel([("profile_id", ASCENDING)], unique=True)
        ]
