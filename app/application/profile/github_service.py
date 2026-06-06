import asyncio
from typing import Dict, List, Optional, Any
from loguru import logger

from app.application.interfaces.github_port import IGitHubPort

class GitHubService:
    """Service that acts as a wrapper around the GitHub Client Adapter."""

    def __init__(self, github_port: IGitHubPort):
        self.github_port = github_port

    async def get_user_info(self, username: str) -> Dict[str, Any]:
        return await self.github_port.fetch_user_info(username)

    async def get_repositories_data(self, username: str) -> List[Dict[str, Any]]:
        """
        Fetches public repositories list for a user.
        For each repository, fetches README and languages concurrently.
        """
        logger.info(f"Fetching public repositories for user: {username}")
        repos = await self.github_port.fetch_public_repositories(username)
        
        # Limit to 50 most recently pushed repositories to avoid API timeouts and rate limit exhaustion
        repos = sorted(repos, key=lambda r: r.get("pushed_at", "") or r.get("updated_at", ""), reverse=True)[:50]
        logger.info(f"Ingesting top {len(repos)} repositories based on activity.")

        async def fetch_repo_details(repo: Dict[str, Any]) -> Dict[str, Any]:
            name = repo.get("name", "")
            description = repo.get("description", "")
            default_branch = repo.get("default_branch", "main")
            topics = repo.get("topics", [])
            last_updated_str = repo.get("pushed_at") or repo.get("updated_at")
            
            # Fetch README and language counts concurrently
            readme_task = self.github_port.fetch_repository_readme(username, name, default_branch)
            languages_task = self.github_port.fetch_repository_languages(username, name)
            
            readme_content, languages = await asyncio.gather(
                readme_task, 
                languages_task, 
                return_exceptions=True
            )
            
            if isinstance(readme_content, Exception):
                logger.warning(f"Failed to fetch README for repository {name}: {str(readme_content)}")
                readme_content = None
            if isinstance(languages, Exception):
                logger.warning(f"Failed to fetch languages for repository {name}: {str(languages)}")
                languages = {}

            return {
                "name": name,
                "description": description,
                "readme_content": readme_content,
                "topics": topics,
                "languages": languages,
                "default_branch": default_branch,
                "last_updated": last_updated_str
            }

        # Run detail fetches concurrently in batches of 5 to avoid overloading connections/rate limits
        sem = asyncio.Semaphore(5)
        
        async def sem_fetch(repo: Dict[str, Any]):
            async with sem:
                return await fetch_repo_details(repo)

        tasks = [sem_fetch(r) for r in repos]
        processed_repos = await asyncio.gather(*tasks)
        return processed_repos
