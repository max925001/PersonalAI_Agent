from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional
from beanie import Document, Indexed
from pydantic import Field

class CallSessionDocument(Document):
    id: UUID = Field(default_factory=uuid4, alias="_id")
    call_sid: Indexed(str, unique=True)
    from_number: str
    to_number: str
    state: str = "CALL_RECEIVED"
    conversation_id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "call_sessions"
        use_revision = False
