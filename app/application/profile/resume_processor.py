import hashlib
import httpx
import re
import unicodedata
import fitz  # PyMuPDF
from typing import Tuple, Optional
from loguru import logger

from app.core.exceptions import ResumeProcessingException
from app.domain.profile.repository_interfaces import IResumeRepository

class ResumeProcessor:
    """Service responsible for downloading, extracting, and normalizing resume PDFs."""

    def __init__(self, resume_repo: IResumeRepository):
        self.resume_repo = resume_repo

    async def download_pdf(self, url: str) -> bytes:
        # Check if URL is actually a local file path
        if not (url.startswith("http://") or url.startswith("https://")):
            logger.info(f"Reading local resume PDF file from: {url}")
            import os
            try:
                if os.path.exists(url):
                    with open(url, "rb") as f:
                        return f.read()
                else:
                    raise FileNotFoundError(f"Local PDF file not found at {url}")
            except Exception as e:
                logger.error(f"Failed to read local PDF file: {str(e)}")
                raise ResumeProcessingException(f"Failed to read local resume PDF file: {str(e)}")

        logger.info(f"Downloading resume PDF from {url}...")
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.content
        except Exception as e:
            logger.error(f"Failed to download resume PDF: {str(e)}")
            raise ResumeProcessingException(f"Failed to download resume PDF from storage: {str(e)}")

    def extract_text_from_pdf(self, pdf_bytes: bytes) -> str:
        logger.info("Extracting text from PDF bytes using PyMuPDF...")
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text()
            
            if not text.strip():
                raise ValueError("Extracted text is empty. PDF might be scanned/image-only.")
            
            return text
        except Exception as e:
            logger.error(f"PyMuPDF text extraction failed: {str(e)}")
            raise ResumeProcessingException(f"Failed to extract text from PDF: {str(e)}")

    def normalize_text(self, text: str) -> str:
        """Cleans extracted text: normalizes unicode, fixes broken lines/hyphenation, and removes extra whitespace."""
        # Normalize Unicode character shapes and ligatures (e.g. fi, fl)
        text = unicodedata.normalize("NFKC", text)
        
        # Remove broken words across lines (e.g., "devel-\noper" -> "developer")
        text = re.sub(r"(\w+)-\n\s*(\w+)", r"\1\2", text)
        
        # Replace broken lines inside sentences while keeping paragraph breaks
        # Map carriage returns to standard newlines
        text = text.replace("\r\n", "\n")
        
        lines = text.split("\n")
        cleaned_lines = []
        
        for line in lines:
            # Remove leading/trailing spaces and collapse multiple spaces within a line
            cleaned_line = re.sub(r"\s+", " ", line.strip())
            if cleaned_line:
                cleaned_lines.append(cleaned_line)
            else:
                cleaned_lines.append("")
        
        # Reconstruct content by joining lines
        reconstructed = "\n".join(cleaned_lines)
        
        # Clean up multi-newline gaps: limit maximum consecutive newlines to 2 (paragraph break)
        reconstructed = re.sub(r"\n{3,}", "\n\n", reconstructed)
        
        return reconstructed.strip()

    def generate_sha256_hash(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    async def process_resume(self, profile_id: str, cloudinary_url: str) -> Tuple[str, str, bool]:
        """
        Downloads and processes the resume.
        Returns a tuple: (extracted_text, content_hash, has_changed)
        """
        pdf_bytes = await self.download_pdf(cloudinary_url)
        raw_text = self.extract_text_from_pdf(pdf_bytes)
        normalized_text = self.normalize_text(raw_text)
        new_hash = self.generate_sha256_hash(normalized_text)
        
        # Check if the resume content hash has changed compared to last upload
        existing_resume = await self.resume_repo.get_by_profile_id(profile_id)
        has_changed = True
        
        if existing_resume and existing_resume.content_hash == new_hash:
            logger.info(f"Resume content hash ({new_hash}) is unchanged. Skipping vector regeneration.")
            has_changed = False
            normalized_text = existing_resume.extracted_text or normalized_text
            
        return normalized_text, new_hash, has_changed
