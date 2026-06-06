import asyncio
from typing import List
from sentence_transformers import SentenceTransformer
from loguru import logger

from app.core.exceptions import EmbeddingException
from app.application.interfaces.embedding_port import IEmbeddingPort

class SentenceTransformersEmbeddingAdapter(IEmbeddingPort):
    """Adapter for generating text embeddings locally using SentenceTransformers."""

    def __init__(self):
        self.model_name = "BAAI/bge-small-en-v1.5"
        logger.info(f"Initializing SentenceTransformers model: {self.model_name}...")
        try:
            self.model = SentenceTransformer(self.model_name)
            logger.info("SentenceTransformers model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load SentenceTransformers model: {str(e)}")
            raise EmbeddingException(f"Failed to initialize local embedding model: {str(e)}")

    @property
    def dimension(self) -> int:
        return 384  # BAAI/bge-small-en-v1.5 returns 384-dimensional vectors

    @property
    def requires_pacing(self) -> bool:
        return False

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        
        try:
            # Run the synchronous model encoding in a thread pool to avoid blocking the event loop
            logger.info(f"Generating local embeddings for {len(texts)} chunks...")
            embeddings = await asyncio.to_thread(
                self.model.encode,
                texts,
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Local embedding generation failed: {str(e)}")
            raise EmbeddingException(f"Failed to generate embeddings: {str(e)}")
