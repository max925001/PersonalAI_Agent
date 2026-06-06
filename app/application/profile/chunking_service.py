import hashlib
from typing import List, Dict, Any
from loguru import logger
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.domain.profile.entities import KnowledgeDocument

class ChunkingService:
    """Service that processes KnowledgeDocuments into chunks using LangChain splitter."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        logger.info(f"ChunkingService initialized with chunk_size={chunk_size}, chunk_overlap={chunk_overlap}")

    def _generate_chunk_hash(self, source_id: str, chunk_index: int, text: str) -> str:
        """Generates a unique SHA256 hash for a specific chunk."""
        hasher = hashlib.sha256()
        hasher.update(f"{source_id}:{chunk_index}:{text}".encode("utf-8"))
        return hasher.hexdigest()

    def chunk_documents(self, documents: List[KnowledgeDocument]) -> List[Dict[str, Any]]:
        """
        Splits a list of KnowledgeDocuments into chunks.
        Deduplicates chunks with identical content hashes and enriches metadata.
        """
        logger.info(f"Splitting {len(documents)} knowledge documents into chunks...")
        processed_chunks: List[Dict[str, Any]] = []
        seen_hashes = set()

        for doc in documents:
            content = doc.content
            # Skip empty content
            if not content.strip():
                continue
                
            # Perform splitting
            splits = self.splitter.split_text(content)
            
            for idx, split_text in enumerate(splits):
                chunk_hash = self._generate_chunk_hash(doc.source_id, idx, split_text)
                
                # Check for duplicates across the pipeline run
                if chunk_hash in seen_hashes:
                    logger.debug(f"Duplicate chunk hash {chunk_hash} detected. Skipping.")
                    continue
                
                seen_hashes.add(chunk_hash)

                # Enrich metadata
                metadata = {
                    "source_type": doc.source_type,
                    "source_id": doc.source_id,
                    "chunk_index": idx,
                    "repository_name": doc.metadata.get("repository_name") or ""
                }

                processed_chunks.append({
                    "text": split_text,
                    "hash": chunk_hash,
                    "metadata": metadata
                })

        logger.info(f"Total chunks created: {len(processed_chunks)}")
        return processed_chunks
