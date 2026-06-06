import uuid
from abc import ABC, abstractmethod
from typing import Optional, List
from app.domain.profile.entities import (
    Profile, Resume, GitHubRepository, Availability,
    KnowledgeDocument, ProcessingStatus, EmbeddingJob
)

class IProfileRepository(ABC):
    @abstractmethod
    async def get_by_id(self, profile_id: uuid.UUID) -> Optional[Profile]:
        pass

    @abstractmethod
    async def save(self, profile: Profile) -> Profile:
        pass

    @abstractmethod
    async def get_current(self) -> Optional[Profile]:
        """Since AI Shivam platform represents ONE candidate only."""
        pass


class IResumeRepository(ABC):
    @abstractmethod
    async def get_by_id(self, resume_id: uuid.UUID) -> Optional[Resume]:
        pass

    @abstractmethod
    async def get_by_profile_id(self, profile_id: uuid.UUID) -> Optional[Resume]:
        pass

    @abstractmethod
    async def save(self, resume: Resume) -> Resume:
        pass


class IGitHubRepositoryRepository(ABC):
    @abstractmethod
    async def get_by_id(self, repo_id: uuid.UUID) -> Optional[GitHubRepository]:
        pass

    @abstractmethod
    async def get_by_profile_id(self, profile_id: uuid.UUID) -> List[GitHubRepository]:
        pass

    @abstractmethod
    async def get_by_profile_and_name(self, profile_id: uuid.UUID, name: str) -> Optional[GitHubRepository]:
        pass

    @abstractmethod
    async def save(self, repo: GitHubRepository) -> GitHubRepository:
        pass

    @abstractmethod
    async def delete_by_profile_except(self, profile_id: uuid.UUID, active_repo_names: List[str]) -> None:
        """Removes repositories that are no longer public/present on GitHub."""
        pass


class IAvailabilityRepository(ABC):
    @abstractmethod
    async def get_by_profile_id(self, profile_id: uuid.UUID) -> List[Availability]:
        pass

    @abstractmethod
    async def save_all(self, availabilities: List[Availability]) -> List[Availability]:
        pass

    @abstractmethod
    async def delete_by_profile_id(self, profile_id: uuid.UUID) -> None:
        pass


class IKnowledgeDocumentRepository(ABC):
    @abstractmethod
    async def get_by_profile_id(self, profile_id: uuid.UUID) -> List[KnowledgeDocument]:
        pass

    @abstractmethod
    async def save(self, doc: KnowledgeDocument) -> KnowledgeDocument:
        pass

    @abstractmethod
    async def delete_by_profile_id(self, profile_id: uuid.UUID) -> None:
        pass


class IProcessingStatusRepository(ABC):
    @abstractmethod
    async def get_by_profile_id(self, profile_id: uuid.UUID) -> Optional[ProcessingStatus]:
        pass

    @abstractmethod
    async def save(self, status: ProcessingStatus) -> ProcessingStatus:
        pass


class IEmbeddingJobRepository(ABC):
    @abstractmethod
    async def get_by_id(self, job_id: uuid.UUID) -> Optional[EmbeddingJob]:
        pass

    @abstractmethod
    async def save(self, job: EmbeddingJob) -> EmbeddingJob:
        pass
