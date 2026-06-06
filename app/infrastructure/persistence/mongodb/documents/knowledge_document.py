from datetime import datetime
from uuid import UUID, uuid4
from beanie import Document
from pydantic import Field
from typing import Optional, Dict, Any
from pymongo import IndexModel, ASCENDING

class KnowledgeDocumentDocument(Document):
    id: UUID = Field(default_factory=uuid4, alias="_id")
    profile_id: UUID
    source_type: str  # resume, repository, additional_information, profile
    source_id: str
    title: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "knowledge_documents"
        use_revision = False
        indexes = [
            IndexModel([("profile_id", ASCENDING)])
        ]
