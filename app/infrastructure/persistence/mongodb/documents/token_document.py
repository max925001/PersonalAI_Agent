from datetime import datetime
from uuid import UUID, uuid4
from beanie import Document, Indexed
from pydantic import Field

class RefreshTokenDocument(Document):
    id: UUID = Field(default_factory=uuid4, alias="_id")
    user_id: UUID = Field(..., index=True)
    token_hash: Indexed(str, unique=True)
    expires_at: datetime
    revoked: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "refresh_tokens"
        use_revision = False