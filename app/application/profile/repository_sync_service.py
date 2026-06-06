import hashlib
import json
import uuid
import dateutil.parser
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple, Optional
from loguru import logger

from app.domain.profile.entities import GitHubRepository
from app.domain.profile.repository_interfaces import IGitHubRepositoryRepository

class RepositorySyncService:
    """Service responsible for syncing fetched GitHub repository data with MongoDB."""

    def __init__(self, repo_repository: IGitHubRepositoryRepository):
        self.repo_repository = repo_repository

    def _compute_repo_hash(self, name: str, description: Optional[str], readme_content: Optional[str], topics: List[str], languages: Dict[str, int]) -> str:
        # Construct a unique serialized representation of the content
        content_dict = {
            "name": name,
            "description": description or "",
            "readme_content": readme_content or "",
            "topics": sorted(topics),
            "languages": sorted(languages.items())
        }
        serialized = json.dumps(content_dict, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    async def sync_repositories(self, profile_id: uuid.UUID, repos_data: List[Dict[str, Any]]) -> Tuple[List[GitHubRepository], bool]:
        """
        Syncs GitHub repository metadata.
        Returns a list of all current repositories and a boolean indicating if changes occurred.
        """
        logger.info(f"Syncing repositories for profile: {profile_id}")
        
        # Get existing repos from db
        existing_repos = await self.repo_repository.get_by_profile_id(profile_id)
        existing_repo_map = {r.name: r for r in existing_repos}

        active_repo_names = []
        any_repo_changed = False
        all_current_repos = []

        for repo_info in repos_data:
            name = repo_info["name"]
            description = repo_info["description"]
            readme_content = repo_info["readme_content"]
            topics = repo_info["topics"]
            languages = repo_info["languages"]
            default_branch = repo_info["default_branch"]
            last_updated_str = repo_info["last_updated"]
            
            # Parse last updated date to timezone-aware UTC datetime
            last_updated = dateutil.parser.parse(last_updated_str) if last_updated_str else datetime.now(timezone.utc)
            if last_updated.tzinfo is None:
                last_updated = last_updated.replace(tzinfo=timezone.utc)

            active_repo_names.append(name)
            content_hash = self._compute_repo_hash(name, description, readme_content, topics, languages)

            existing_repo = existing_repo_map.get(name)
            
            if existing_repo:
                if existing_repo.content_hash == content_hash:
                    # Skip update, content hash matches
                    logger.debug(f"Repo {name} has not changed. Skipping database update.")
                    all_current_repos.append(existing_repo)
                else:
                    # Content has changed
                    logger.info(f"Repo {name} content changed. Updating database record.")
                    existing_repo.description = description
                    existing_repo.readme_content = readme_content
                    existing_repo.topics = topics
                    existing_repo.languages = languages
                    existing_repo.default_branch = default_branch
                    existing_repo.last_updated = last_updated
                    existing_repo.content_hash = content_hash
                    existing_repo.updated_at = datetime.now(timezone.utc)
                    
                    await self.repo_repository.save(existing_repo)
                    any_repo_changed = True
                    all_current_repos.append(existing_repo)
            else:
                # New repository found
                logger.info(f"New repo {name} discovered. Inserting database record.")
                new_repo = GitHubRepository(
                    profile_id=profile_id,
                    name=name,
                    description=description,
                    readme_content=readme_content,
                    topics=topics,
                    languages=languages,
                    default_branch=default_branch,
                    last_updated=last_updated,
                    content_hash=content_hash
                )
                await self.repo_repository.save(new_repo)
                any_repo_changed = True
                all_current_repos.append(new_repo)

        # Detect deleted/private repositories
        deleted_count = 0
        for name in list(existing_repo_map.keys()):
            if name not in active_repo_names:
                logger.info(f"Repo {name} is no longer public/active on GitHub. Deleting DB record.")
                deleted_count += 1
                any_repo_changed = True

        if deleted_count > 0:
            await self.repo_repository.delete_by_profile_except(profile_id, active_repo_names)

        return all_current_repos, any_repo_changed
