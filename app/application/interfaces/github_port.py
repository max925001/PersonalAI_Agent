from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any

class IGitHubPort(ABC):
    """Port contract for GitHub API client adapter."""

    @abstractmethod
    async def fetch_user_info(self, username: str) -> Dict[str, Any]:
        """Fetches basic profile info for a GitHub user."""
        pass

    @abstractmethod
    async def fetch_public_repositories(self, username: str) -> List[Dict[str, Any]]:
        """Fetches a list of public repositories for a GitHub user."""
        pass

    @abstractmethod
    async def fetch_repository_readme(self, username: str, repo_name: str, default_branch: str = "main") -> Optional[str]:
        """Fetches and decodes the README content for a specific repository."""
        pass

    @abstractmethod
    async def fetch_repository_languages(self, username: str, repo_name: str) -> Dict[str, int]:
        """Fetches the languages dictionary (language name -> byte count) for a specific repository."""
        pass
