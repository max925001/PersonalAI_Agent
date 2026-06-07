import asyncio
import sys
from loguru import logger
import uuid

# Set PYTHONPATH
import os
sys.path.append(os.getcwd())

from app.core.config import settings
from app.infrastructure.persistence.mongodb.database import init_database, close_connections
from app.infrastructure.persistence.mongodb.repositories.knowledge_document_repository import BeanieKnowledgeDocumentRepository
from app.infrastructure.persistence.mongodb.repositories.profile_repository import BeanieProfileRepository
from app.application.profile.chunking_service import ChunkingService
from app.application.profile.embedding_service import EmbeddingService
from app.infrastructure.web.dependencies import get_embedding_port
from app.infrastructure.persistence.qdrant.qdrant_adapter import QdrantAdapter

async def main():
    profile_id_str = "9b0a9ed8-2783-49cb-8c32-97355accfd15"
    profile_id = uuid.UUID(profile_id_str)
    
    logger.info("Initializing Database...")
    await init_database()
    
    try:
        logger.info(f"Fetching knowledge documents for profile: {profile_id_str}...")
        knowledge_repo = BeanieKnowledgeDocumentRepository()
        docs = await knowledge_repo.get_by_profile_id(profile_id)
        logger.info(f"Retrieved {len(docs)} knowledge documents.")
        
        if not docs:
            logger.error("No knowledge documents found for this profile in database.")
            return
            
        logger.info("Running chunking service...")
        chunking_service = ChunkingService()
        chunks = chunking_service.chunk_documents(docs)
        logger.info(f"Generated {len(chunks)} chunks.")
        
        logger.info("Loading HuggingFace/configured adapter & embedding chunks...")
        embedding_adapter = get_embedding_port()
        embedding_service = EmbeddingService(embedding_adapter)
        embedded_chunks = await embedding_service.embed_chunks(chunks)
        
        logger.info("Initializing Qdrant Adapter...")
        qdrant_adapter = QdrantAdapter()
        
        logger.info("Ensuring Qdrant collection...")
        await qdrant_adapter.ensure_collection('shivam_knowledge_base', 384)
        
        logger.info(f"Running upsert for {len(embedded_chunks)} points...")
        await qdrant_adapter.upsert_chunks('shivam_knowledge_base', embedded_chunks, profile_id_str)
        logger.info("✅ SUCCESS! Ingestion upsert completed without errors.")
        
    except Exception as e:
        logger.error("❌ Diagnostic run failed!")
        import traceback
        traceback.print_exc()
    finally:
        close_connections()

if __name__ == "__main__":
    asyncio.run(main())
