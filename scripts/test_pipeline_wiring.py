import asyncio
import sys
import uuid
from datetime import datetime, timezone
from loguru import logger

from app.core.config import settings
from app.infrastructure.persistence.mongodb.database import init_database, close_connections

# Import Repositories
from app.infrastructure.persistence.mongodb.repositories.profile_repository import BeanieProfileRepository
from app.infrastructure.persistence.mongodb.repositories.resume_repository import BeanieResumeRepository
from app.infrastructure.persistence.mongodb.repositories.github_repo_repository import BeanieGitHubRepositoryRepository
from app.infrastructure.persistence.mongodb.repositories.availability_repository import BeanieAvailabilityRepository
from app.infrastructure.persistence.mongodb.repositories.knowledge_document_repository import BeanieKnowledgeDocumentRepository
from app.infrastructure.persistence.mongodb.repositories.processing_status_repository import BeanieProcessingStatusRepository
from app.infrastructure.persistence.mongodb.repositories.embedding_job_repository import BeanieEmbeddingJobRepository

# Import Adapters
from app.infrastructure.adapters.storage.cloudinary_adapter import CloudinaryStorageAdapter
from app.infrastructure.adapters.github.github_client_adapter import GitHubClientAdapter
from app.infrastructure.web.dependencies import get_embedding_port
from app.infrastructure.persistence.qdrant.qdrant_adapter import QdrantAdapter

# Import Services
from app.application.profile.resume_processor import ResumeProcessor
from app.application.profile.github_service import GitHubService
from app.application.profile.repository_sync_service import RepositorySyncService
from app.application.profile.knowledge_document_service import KnowledgeDocumentService
from app.application.profile.chunking_service import ChunkingService
from app.application.profile.embedding_service import EmbeddingService
from app.application.profile.qdrant_service import QdrantService
from app.application.profile.scheduling_service import SchedulingService
from app.application.profile.background_orchestrator import BackgroundJobOrchestrator

async def main():
    logger.info("Initializing Beanie ODM with test MongoDB connection...")
    try:
        await init_database()
        logger.info("MongoDB initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        logger.warning("Continuing wiring test with mock DB interface...")

    try:
        logger.info("Wiring Profile Ingestion Pipeline dependencies...")
        
        # 1. Instantiate Repositories
        profile_repo = BeanieProfileRepository()
        resume_repo = BeanieResumeRepository()
        github_repo = BeanieGitHubRepositoryRepository()
        availability_repo = BeanieAvailabilityRepository()
        knowledge_repo = BeanieKnowledgeDocumentRepository()
        status_repo = BeanieProcessingStatusRepository()
        embedding_job_repo = BeanieEmbeddingJobRepository()
        
        # 2. Instantiate Adapters
        storage_adapter = CloudinaryStorageAdapter()
        github_adapter = GitHubClientAdapter()
        embedding_adapter = get_embedding_port()
        qdrant_adapter = QdrantAdapter()
        
        # 3. Instantiate Services
        resume_processor = ResumeProcessor(resume_repo)
        github_service = GitHubService(github_adapter)
        sync_service = RepositorySyncService(github_repo)
        knowledge_service = KnowledgeDocumentService(knowledge_repo)
        chunking_service = ChunkingService()
        embedding_service = EmbeddingService(embedding_adapter)
        qdrant_service = QdrantService(qdrant_adapter)
        scheduling_service = SchedulingService(availability_repo)
        
        # 4. Instantiate Orchestrator
        orchestrator = BackgroundJobOrchestrator(
            profile_repo=profile_repo,
            resume_repo=resume_repo,
            status_repo=status_repo,
            embedding_job_repo=embedding_job_repo,
            resume_processor=resume_processor,
            github_service=github_service,
            sync_service=sync_service,
            knowledge_service=knowledge_service,
            chunking_service=chunking_service,
            embedding_service=embedding_service,
            qdrant_service=qdrant_service,
            embedding_port=embedding_adapter
        )
        
        logger.info("✅ All components wired successfully!")
        
    except Exception as e:
        logger.error(f"❌ Wiring failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
        
    finally:
        close_connections()

if __name__ == "__main__":
    asyncio.run(main())
