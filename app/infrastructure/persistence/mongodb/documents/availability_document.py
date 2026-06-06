from typing import Optional
from datetime import datetime
from uuid import UUID, uuid4
from beanie import Document
from pydantic import Field
from pymongo import IndexModel, ASCENDING

class AvailabilityDocument(Document):
    id: UUID = Field(default_factory=uuid4, alias="_id")
    profile_id: UUID
    slot: datetime  # ISO-8601 UTC timestamp
    is_booked: bool = False
    booked_by_name: Optional[str] = None
    booked_by_email: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "availabilities"
        use_revision = False
        indexes = [
            IndexModel([("profile_id", ASCENDING)])
        ]
