from datetime import datetime
from uuid import UUID, uuid4
from beanie import Document
from pydantic import Field
from pymongo import IndexModel, ASCENDING

class ConversationDocument(Document):
    id: UUID = Field(default_factory=uuid4, alias="_id")
    session_id: UUID
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "conversations"
        use_revision = False
        indexes = [
            IndexModel([("session_id", ASCENDING)], unique=True)
        ]
