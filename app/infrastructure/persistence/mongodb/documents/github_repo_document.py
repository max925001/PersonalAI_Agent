from datetime import datetime
from uuid import UUID, uuid4
from beanie import Document
from pydantic import Field
from typing import Optional, List, Dict
from pymongo import IndexModel, ASCENDING

class GitHubRepositoryDocument(Document):
    id: UUID = Field(default_factory=uuid4, alias="_id")
    profile_id: UUID
    name: str
    description: Optional[str] = None
    readme_content: Optional[str] = None
    topics: List[str] = Field(default_factory=list)
    languages: Dict[str, int] = Field(default_factory=dict)
    default_branch: str = "main"
    last_updated: datetime
    content_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "github_repositories"
        use_revision = False
        indexes = [
            IndexModel([("profile_id", ASCENDING)]),
            IndexModel([("name", ASCENDING)]),
            IndexModel([("profile_id", ASCENDING), ("name", ASCENDING)])
        ]
