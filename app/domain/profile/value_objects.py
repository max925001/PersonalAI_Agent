from dataclasses import dataclass
import re

@dataclass(frozen=True)
class GitHubUrl:
    """Domain representation of a validated GitHub URL."""
    value: str

    def __post_init__(self):
        cleaned = self.value.strip()
        # Pattern to match: http(s)://(www.)github.com/username
        pattern = r"^https?://(www\.)?github\.com/[a-zA-Z0-9-_\.]+/?$"
        if not re.match(pattern, cleaned):
            raise ValueError("Invalid GitHub profile URL")
        
        # Keep canonical URL format
        object.__setattr__(self, "value", cleaned)

    @property
    def username(self) -> str:
        """Extracts username from the GitHub URL."""
        parts = self.value.rstrip("/").split("/")
        return parts[-1]


@dataclass(frozen=True)
class ContentHash:
    """Domain representation of a SHA256 content hash."""
    value: str

    def __post_init__(self):
        cleaned = self.value.strip().lower()
        if not re.match(r"^[a-f0-9]{64}$", cleaned):
            raise ValueError("Invalid SHA256 hash format")
        object.__setattr__(self, "value", cleaned)
