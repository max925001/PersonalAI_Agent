import asyncio
from typing import Dict
import cloudinary
import cloudinary.uploader
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings
from app.core.exceptions import CloudinaryException
from app.application.interfaces.storage_port import IStoragePort

class CloudinaryStorageAdapter(IStoragePort):
    """Cloudinary file storage adapter implementing IStoragePort."""

    def __init__(self):
        # Configure cloudinary credentials on initialization
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
            secure=True
        )
        logger.info("Cloudinary storage adapter configured successfully.")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    async def _execute_upload(self, file_content: bytes, folder: str, filename: str) -> Dict[str, str]:
        # Using asyncio.to_thread to run sync Cloudinary SDK call in thread pool to prevent blocking the event loop
        loop = asyncio.get_running_loop()
        logger.info(f"Uploading file {filename} to Cloudinary folder {folder}...")
        
        # Upload options
        options = {
            "folder": folder,
            "resource_type": "raw",
            "overwrite": True
        }
        
        # We can pass raw file bytes to the upload function
        result = await loop.run_in_executor(
            None,
            lambda: cloudinary.uploader.upload(file_content, **options)
        )
        
        url = result.get("secure_url") or result.get("url")
        public_id = result.get("public_id")
        
        if not url or not public_id:
            raise Exception("Cloudinary response missing secure_url or public_id")

        return {
            "url": url,
            "public_id": public_id
        }

    async def upload_file(self, file_content: bytes, filename: str, folder: str = "ai_shivam/resumes") -> Dict[str, str]:
        try:
            return await self._execute_upload(file_content, folder, filename)
        except Exception as e:
            logger.error(f"Failed to upload file to Cloudinary: {str(e)}")
            raise CloudinaryException(f"Failed to upload resume file to Cloudinary: {str(e)}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    async def _execute_delete(self, public_id: str) -> bool:
        loop = asyncio.get_running_loop()
        logger.info(f"Deleting file with public_id {public_id} from Cloudinary...")
        
        result = await loop.run_in_executor(
            None,
            lambda: cloudinary.uploader.destroy(public_id, invalidate=True, resource_type="raw")
        )
        
        result_status = result.get("result")
        if result_status != "ok" and result_status != "not found":
            raise Exception(f"Cloudinary destroy returned unexpected status: {result_status}")
            
        return True

    async def delete_file(self, public_id: str) -> bool:
        try:
            return await self._execute_delete(public_id)
        except Exception as e:
            logger.error(f"Failed to delete file from Cloudinary: {str(e)}")
            raise CloudinaryException(f"Failed to delete file from Cloudinary: {str(e)}")

    async def replace_file(self, old_public_id: str, new_file_content: bytes, filename: str, folder: str = "ai_shivam/resumes") -> Dict[str, str]:
        logger.info(f"Replacing file {old_public_id} in Cloudinary...")
        try:
            # Delete old file first (non-blocking)
            try:
                await self.delete_file(old_public_id)
            except Exception as delete_err:
                # Log delete error but continue to upload the new file
                logger.warning(f"Could not delete old file {old_public_id} during replacement: {str(delete_err)}")

            # Upload new file
            return await self.upload_file(new_file_content, filename, folder)
        except Exception as e:
            logger.error(f"Failed to replace file in Cloudinary: {str(e)}")
            raise CloudinaryException(f"Failed to replace file in Cloudinary: {str(e)}")
