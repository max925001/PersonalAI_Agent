import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

class Profile:
    """Domain model representing a candidate's profile."""
    def __init__(
        self,
        github_url: str,
        additional_information: Optional[str] = None,
        id: Optional[uuid.UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.id = id or uuid.uuid4()
        self.github_url = github_url
        self.additional_information = additional_information
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)


class Resume:
    """Domain model representing a candidate's resume."""
    def __init__(
        self,
        profile_id: uuid.UUID,
        cloudinary_url: str,
        cloudinary_public_id: str,
        content_hash: str,
        extracted_text: Optional[str] = None,
        id: Optional[uuid.UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.id = id or uuid.uuid4()
        self.profile_id = profile_id
        self.cloudinary_url = cloudinary_url
        self.cloudinary_public_id = cloudinary_public_id
        self.content_hash = content_hash
        self.extracted_text = extracted_text
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)


class GitHubRepository:
    """Domain model representing a synced GitHub repository."""
    def __init__(
        self,
        profile_id: uuid.UUID,
        name: str,
        description: Optional[str],
        readme_content: Optional[str],
        topics: List[str],
        languages: Dict[str, int],
        default_branch: str,
        last_updated: datetime,
        content_hash: str,
        id: Optional[uuid.UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.id = id or uuid.uuid4()
        self.profile_id = profile_id
        self.name = name
        self.description = description
        self.readme_content = readme_content
        self.topics = topics
        self.languages = languages
        self.default_branch = default_branch
        self.last_updated = last_updated
        self.content_hash = content_hash
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)


class Availability:
    """Domain model representing an interview slot."""
    def __init__(
        self,
        profile_id: uuid.UUID,
        slot: datetime,
        is_booked: bool = False,
        booked_by_name: Optional[str] = None,
        booked_by_email: Optional[str] = None,
        id: Optional[uuid.UUID] = None,
        created_at: Optional[datetime] = None
    ):
        self.id = id or uuid.uuid4()
        self.profile_id = profile_id
        self.slot = slot
        self.is_booked = is_booked
        self.booked_by_name = booked_by_name
        self.booked_by_email = booked_by_email
        self.created_at = created_at or datetime.now(timezone.utc)


class KnowledgeDocument:
    """Domain model representing a normalized document before chunking."""
    def __init__(
        self,
        profile_id: uuid.UUID,
        source_type: str,  # resume, repository, additional_information, profile
        source_id: str,
        title: str,
        content: str,
        metadata: Dict[str, Any],
        id: Optional[uuid.UUID] = None,
        created_at: Optional[datetime] = None
    ):
        self.id = id or uuid.uuid4()
        self.profile_id = profile_id
        self.source_type = source_type
        self.source_id = source_id
        self.title = title
        self.content = content
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.now(timezone.utc)


class ProcessingStatus:
    """Domain model tracking profile ingestion steps."""
    def __init__(
        self,
        profile_id: uuid.UUID,
        current_step: str,
        progress: float,
        status: str,  # PENDING, PROCESSING, COMPLETED, FAILED
        error_message: Optional[str] = None,
        id: Optional[uuid.UUID] = None,
        last_updated: Optional[datetime] = None
    ):
        self.id = id or uuid.uuid4()
        self.profile_id = profile_id
        self.current_step = current_step
        self.progress = progress
        self.status = status
        self.error_message = error_message
        self.last_updated = last_updated or datetime.now(timezone.utc)


class EmbeddingJob:
    """Domain model representing individual embedding batch sync operations."""
    def __init__(
        self,
        profile_id: uuid.UUID,
        status: str,  # PENDING, PROCESSING, COMPLETED, FAILED
        error_message: Optional[str] = None,
        id: Optional[uuid.UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.id = id or uuid.uuid4()
        self.profile_id = profile_id
        self.status = status
        self.error_message = error_message
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)
