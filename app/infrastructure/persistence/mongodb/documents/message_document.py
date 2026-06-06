from datetime import datetime
from uuid import UUID, uuid4
from beanie import Document
from pydantic import Field
from pymongo import IndexModel, ASCENDING

class MessageDocument(Document):
    id: UUID = Field(default_factory=uuid4, alias="_id")
    session_id: UUID
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "messages"
        use_revision = False
        indexes = [
            IndexModel([("session_id", ASCENDING), ("timestamp", ASCENDING)])
        ]
