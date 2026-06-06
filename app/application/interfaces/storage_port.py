from abc import ABC, abstractmethod
from typing import Dict

class IStoragePort(ABC):
    """Port contract for file storage adapters (e.g. Cloudinary, S3)."""

    @abstractmethod
    async def upload_file(self, file_content: bytes, filename: str, folder: str = "ai_shivam/resumes") -> Dict[str, str]:
        """Uploads a file to storage and returns metadata containing 'url' and 'public_id'."""
        pass

    @abstractmethod
    async def delete_file(self, public_id: str) -> bool:
        """Deletes a file from storage by its public ID."""
        pass

    @abstractmethod
    async def replace_file(self, old_public_id: str, new_file_content: bytes, filename: str, folder: str = "ai_shivam/resumes") -> Dict[str, str]:
        """Deletes the old file and uploads a new one, returning the new file's metadata."""
        pass
