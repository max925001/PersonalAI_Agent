import base64
import httpx
from typing import Dict, List, Optional, Any
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings
from app.core.exceptions import GitHubException
from app.application.interfaces.github_port import IGitHubPort

class GitHubClientAdapter(IGitHubPort):
    """HTTPX-based client implementation for the GitHub API."""

    def __init__(self):
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AI-Shivam-Platform"
        }
        if settings.GITHUB_TOKEN:
            self.headers["Authorization"] = f"token {settings.GITHUB_TOKEN}"
            logger.info("GitHub adapter initialized with Personal Access Token.")
        else:
            logger.warning("GitHub adapter initialized without token (unauthenticated rate limits apply).")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(httpx.HTTPError),
        reraise=True
    )
    async def _request(self, method: str, path: str, params: Optional[Dict[str, Any]] = None) -> httpx.Response:
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        async with httpx.AsyncClient(headers=self.headers, timeout=10.0) as client:
            try:
                response = await client.request(method, url, params=params)
                
                # Check for rate limit issues
                if response.status_code in (403, 429):
                    reset_time = response.headers.get("X-RateLimit-Reset")
                    logger.error(f"GitHub API rate limit hit. Reset time: {reset_time}")
                    raise GitHubException(
                        f"GitHub API rate limit reached. Reset at UTC timestamp: {reset_time}",
                        code="GITHUB_RATE_LIMIT"
                    )
                
                response.raise_for_status()
                return response
            except httpx.HTTPStatusError as e:
                # Handle standard HTTP status errors
                if e.response.status_code == 404:
                    raise e # Let caller handle 404s (e.g. repo not found or README not found)
                raise GitHubException(
                    f"GitHub API returned error status {e.response.status_code}: {e.response.text}",
                    code="GITHUB_API_ERROR"
                ) from e
            except httpx.RequestError as e:
                raise GitHubException(
                    f"GitHub API request failed: {str(e)}",
                    code="GITHUB_CONNECTION_ERROR"
                ) from e

    async def fetch_user_info(self, username: str) -> Dict[str, Any]:
        try:
            response = await self._request("GET", f"/users/{username}")
            return response.json()
        except Exception as e:
            if isinstance(e, GitHubException):
                raise e
            raise GitHubException(f"Failed to fetch user info for {username}: {str(e)}")

    async def fetch_public_repositories(self, username: str) -> List[Dict[str, Any]]:
        try:
            # Fetch up to 100 repositories, sorted by most recently updated
            response = await self._request(
                "GET", 
                f"/users/{username}/repos", 
                params={"type": "owner", "per_page": 100, "sort": "pushed"}
            )
            return response.json()
        except Exception as e:
            if isinstance(e, GitHubException):
                raise e
            raise GitHubException(f"Failed to fetch repositories for {username}: {str(e)}")

    async def fetch_repository_readme(self, username: str, repo_name: str, default_branch: str = "main") -> Optional[str]:
        try:
            # Retrieve README content structure
            response = await self._request("GET", f"/repos/{username}/{repo_name}/readme")
            data = response.json()
            
            content_b64 = data.get("content", "")
            encoding = data.get("encoding", "")
            
            if encoding == "base64" and content_b64:
                # Replace newlines in base64 string before decoding
                decoded_bytes = base64.b64decode(content_b64.replace("\n", ""))
                return decoded_bytes.decode("utf-8", errors="ignore")
            
            return None
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"README file not found for repository {username}/{repo_name}")
                return None
            raise GitHubException(f"Failed to fetch README: {e.response.text}")
        except Exception as e:
            if isinstance(e, GitHubException):
                raise e
            raise GitHubException(f"Failed to fetch README for repository {repo_name}: {str(e)}")

    async def fetch_repository_languages(self, username: str, repo_name: str) -> Dict[str, int]:
        try:
            response = await self._request("GET", f"/repos/{username}/{repo_name}/languages")
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return {}
            raise GitHubException(f"Failed to fetch languages: {e.response.text}")
        except Exception as e:
            if isinstance(e, GitHubException):
                raise e
            raise GitHubException(f"Failed to fetch languages for repository {repo_name}: {str(e)}")
