import uuid
from datetime import datetime, timezone
from typing import Optional

class Conversation:
    """Domain model representing a chat conversation session."""
    def __init__(
        self,
        session_id: uuid.UUID,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        id: Optional[uuid.UUID] = None
    ):
        self.id = id or uuid.uuid4()
        self.session_id = session_id
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)


class Message:
    """Domain model representing an individual message in a conversation session."""
    def __init__(
        self,
        session_id: uuid.UUID,
        role: str,  # "user" or "assistant"
        content: str,
        timestamp: Optional[datetime] = None,
        id: Optional[uuid.UUID] = None
    ):
        self.id = id or uuid.uuid4()
        self.session_id = session_id
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.now(timezone.utc)
