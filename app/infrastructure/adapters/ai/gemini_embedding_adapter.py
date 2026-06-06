import asyncio
from typing import List
import google.generativeai as genai
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings
from app.core.exceptions import EmbeddingException
from app.application.interfaces.embedding_port import IEmbeddingPort

class GeminiEmbeddingAdapter(IEmbeddingPort):
    """Adapter for Google Gemini Embedding Model."""

    def __init__(self):
        # Configure API key: support both GEMINI_API_KEY and GOOGLE_API_KEY
        api_key = settings.GEMINI_API_KEY
        if not api_key or api_key == "gemini-key":
            api_key = settings.GOOGLE_API_KEY

        if not api_key or api_key == "gemini-key":
            logger.warning("Neither GEMINI_API_KEY nor GOOGLE_API_KEY is configured correctly. Embedding calls will fail.")
        else:
            logger.info("Initializing Google Gemini API connection...")
            genai.configure(api_key=api_key)
            
        self.model_name = "models/gemini-embedding-2"
        logger.info(f"Gemini embedding adapter initialized using model: {self.model_name}")

    @property
    def dimension(self) -> int:
        return 3072  # models/gemini-embedding-2 returns 3072-dimensional vectors

    @retry(
        stop=stop_after_attempt(8),
        wait=wait_exponential(multiplier=2, min=5, max=60),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    async def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        # Run sync API call in executor to avoid blocking the asyncio event loop
        loop = asyncio.get_running_loop()
        logger.info(f"Sending batch request to Gemini API with {len(texts)} chunks...")
        
        result = await loop.run_in_executor(
            None,
            lambda: genai.embed_content(
                model=self.model_name,
                content=texts,
                task_type="retrieval_document"
            )
        )
        
        # Structure of response from genai.embed_content:
        # {'embedding': [[f1, f2, ...], [f1, f2, ...]]}
        embeddings = result.get("embedding")
        if not embeddings:
            raise Exception("Gemini embedding API returned empty or invalid response")
            
        return embeddings

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        
        try:
            return await self._embed_batch(texts)
        except Exception as e:
            logger.error(f"Failed to generate embeddings from Gemini: {str(e)}")
            raise EmbeddingException(f"Failed to generate embeddings from Gemini API: {str(e)}")
