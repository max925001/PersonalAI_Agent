import asyncio
from typing import List, Dict, Any
from loguru import logger

from app.application.interfaces.embedding_port import IEmbeddingPort

class EmbeddingService:
    """Service that coordinates batching chunk texts and generating their vector embeddings."""

    def __init__(self, embedding_port: IEmbeddingPort, batch_size: int = 20):
        self.embedding_port = embedding_port
        self.batch_size = batch_size
        logger.info(f"EmbeddingService initialized with batch_size={batch_size}")

    async def embed_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
         Extracts texts from chunks that do not already have vectors, batches them, 
        requests embeddings, and maps the resulting vectors back to the chunk dictionaries.
        """
        if not chunks:
            logger.info("No chunks provided for embedding.")
            return []

        chunks_to_embed = [c for c in chunks if c.get("vector") is None]
        total_to_embed = len(chunks_to_embed)
        
        logger.info(f"Total chunks: {len(chunks)}, Chunks needing embeddings: {total_to_embed} (skipped {len(chunks) - total_to_embed} cached vectors)")
        
        if total_to_embed > 0:
            texts_to_embed = [c["text"] for c in chunks_to_embed]
            all_vectors: List[List[float]] = []

            logger.info(f"Generating embeddings for {total_to_embed} chunks in batches of {self.batch_size}...")

            for i in range(0, total_to_embed, self.batch_size):
                batch_texts = texts_to_embed[i : i + self.batch_size]
                logger.debug(f"Processing batch {i // self.batch_size + 1} ({len(batch_texts)} texts)")
                
                # Fetch embeddings for the batch
                batch_vectors = await self.embedding_port.generate_embeddings(batch_texts)
                all_vectors.extend(batch_vectors)

                # Sleep between batches if this is not the last batch and the adapter requires pacing
                if self.embedding_port.requires_pacing and i + self.batch_size < total_to_embed:
                    sleep_duration = 15.0
                    logger.info(f"Sleeping for {sleep_duration}s to respect API rate limits...")
                    await asyncio.sleep(sleep_duration)

            # Verification step to ensure alignment
            if len(all_vectors) != total_to_embed:
                raise ValueError(
                    f"Embedding vector counts mismatch. Expected {total_to_embed}, got {len(all_vectors)}."
                )

            # Assign vectors to the chunks that were embedded
            for idx, chunk in enumerate(chunks_to_embed):
                chunk["vector"] = all_vectors[idx]

        logger.info(f"Successfully prepared vectors for all {len(chunks)} chunks.")
        return chunks
