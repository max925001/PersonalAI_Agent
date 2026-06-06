from datetime import datetime
from uuid import UUID, uuid4
from beanie import Document
from pydantic import Field
from typing import Optional

class ProfileDocument(Document):
    id: UUID = Field(default_factory=uuid4, alias="_id")
    github_url: str
    additional_information: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "profiles"
        use_revision = False
