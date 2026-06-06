import uuid
from typing import Optional, List
from app.domain.profile.entities import GitHubRepository
from app.domain.profile.repository_interfaces import IGitHubRepositoryRepository
from app.infrastructure.persistence.mongodb.documents.github_repo_document import GitHubRepositoryDocument

class BeanieGitHubRepositoryRepository(IGitHubRepositoryRepository):
    async def get_by_id(self, repo_id: uuid.UUID) -> Optional[GitHubRepository]:
        doc = await GitHubRepositoryDocument.get(repo_id)
        return self._to_domain(doc) if doc else None

    async def get_by_profile_id(self, profile_id: uuid.UUID) -> List[GitHubRepository]:
        docs = await GitHubRepositoryDocument.find(GitHubRepositoryDocument.profile_id == profile_id).to_list()
        return [self._to_domain(doc) for doc in docs]

    async def get_by_profile_and_name(self, profile_id: uuid.UUID, name: str) -> Optional[GitHubRepository]:
        doc = await GitHubRepositoryDocument.find_one(
            GitHubRepositoryDocument.profile_id == profile_id,
            GitHubRepositoryDocument.name == name
        )
        return self._to_domain(doc) if doc else None

    async def save(self, repo: GitHubRepository) -> GitHubRepository:
        doc = await GitHubRepositoryDocument.get(repo.id)
        if not doc:
            doc = GitHubRepositoryDocument(
                id=repo.id,
                profile_id=repo.profile_id,
                name=repo.name,
                description=repo.description,
                readme_content=repo.readme_content,
                topics=repo.topics,
                languages=repo.languages,
                default_branch=repo.default_branch,
                last_updated=repo.last_updated,
                content_hash=repo.content_hash,
                created_at=repo.created_at,
                updated_at=repo.updated_at
            )
        else:
            doc.name = repo.name
            doc.description = repo.description
            doc.readme_content = repo.readme_content
            doc.topics = repo.topics
            doc.languages = repo.languages
            doc.default_branch = repo.default_branch
            doc.last_updated = repo.last_updated
            doc.content_hash = repo.content_hash
            doc.updated_at = repo.updated_at

        await doc.save()
        return repo

    async def delete_by_profile_except(self, profile_id: uuid.UUID, active_repo_names: List[str]) -> None:
        # Delete any GitHub repo doc for this profile that is NOT in the active_repo_names
        await GitHubRepositoryDocument.find(
            GitHubRepositoryDocument.profile_id == profile_id,
            GitHubRepositoryDocument.name not in active_repo_names
        ).delete()

    def _to_domain(self, doc: GitHubRepositoryDocument) -> GitHubRepository:
        return GitHubRepository(
            id=doc.id,
            profile_id=doc.profile_id,
            name=doc.name,
            description=doc.description,
            readme_content=doc.readme_content,
            topics=doc.topics,
            languages=doc.languages,
            default_branch=doc.default_branch,
            last_updated=doc.last_updated,
            content_hash=doc.content_hash,
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )
