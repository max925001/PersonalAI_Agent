import asyncio
import sys
import os
import uuid
import shutil
from loguru import logger

# Set PYTHONPATH
sys.path.append(os.getcwd())

from app.core.config import settings
from app.infrastructure.persistence.mongodb.database import init_database, close_connections
from app.infrastructure.persistence.mongodb.repositories.profile_repository import BeanieProfileRepository
from app.infrastructure.persistence.mongodb.repositories.resume_repository import BeanieResumeRepository
from app.infrastructure.persistence.mongodb.repositories.processing_status_repository import BeanieProcessingStatusRepository
from app.infrastructure.persistence.mongodb.repositories.embedding_job_repository import BeanieEmbeddingJobRepository
from app.infrastructure.persistence.mongodb.repositories.knowledge_document_repository import BeanieKnowledgeDocumentRepository
from app.infrastructure.web.dependencies import get_embedding_port
from app.infrastructure.persistence.qdrant.qdrant_adapter import QdrantAdapter
from app.application.profile.resume_processor import ResumeProcessor
from app.application.profile.github_service import GitHubService
from app.application.profile.repository_sync_service import RepositorySyncService
from app.application.profile.knowledge_document_service import KnowledgeDocumentService
from app.application.profile.chunking_service import ChunkingService
from app.application.profile.embedding_service import EmbeddingService
from app.application.profile.qdrant_service import QdrantService
from app.application.profile.background_orchestrator import BackgroundJobOrchestrator
from app.domain.profile.entities import Profile as DomainProfile

async def main():
    logger.info("Initializing Database...")
    await init_database()
    
    # Setup test file
    test_pdf_source = "C:/Users/shiva/OneDrive/Desktop/Shivam_Pandey_Resume_updated.pdf"
    if not os.path.exists(test_pdf_source):
        logger.error(f"Source test PDF not found at {test_pdf_source}")
        close_connections()
        return

    # Create repositories
    profile_repo = BeanieProfileRepository()
    resume_repo = BeanieResumeRepository()
    status_repo = BeanieProcessingStatusRepository()
    embedding_job_repo = BeanieEmbeddingJobRepository()
    knowledge_repo = BeanieKnowledgeDocumentRepository()
    
    # Create Services/Adapters
    from app.infrastructure.adapters.github.github_client_adapter import GitHubClientAdapter
    github_adapter = GitHubClientAdapter()
    
    resume_processor = ResumeProcessor(resume_repo)
    github_service = GitHubService(github_adapter)
    
    from app.infrastructure.persistence.mongodb.repositories.github_repo_repository import BeanieGitHubRepositoryRepository
    github_repo_repository = BeanieGitHubRepositoryRepository()
    sync_service = RepositorySyncService(github_repo_repository)
    
    knowledge_service = KnowledgeDocumentService(knowledge_repo)
    chunking_service = ChunkingService()
    
    embedding_adapter = get_embedding_port()
    embedding_service = EmbeddingService(embedding_adapter)
    
    qdrant_adapter = QdrantAdapter()
    qdrant_service = QdrantService(qdrant_adapter)
    
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

    # 1. Create Profile Entity
    logger.info("Creating domain profile...")
    github_url = "https://github.com/max925001"
    profile = DomainProfile(
        github_url=github_url,
        additional_information="Local PDF Ingestion Test Profile"
    )
    await profile_repo.save(profile)
    profile_id = profile.id
    logger.info(f"Test Profile ID: {profile_id}")

    # 2. Copy test PDF to uploads/{profile_id}.pdf
    os.makedirs("uploads", exist_ok=True)
    pdf_dest = f"uploads/{profile_id}.pdf"
    logger.info(f"Copying PDF file to local server uploads path: {pdf_dest}")
    shutil.copy(test_pdf_source, pdf_dest)
    
    # Read file bytes
    with open(pdf_dest, "rb") as f:
        file_bytes = f.read()

    # 3. Trigger Ingestion
    logger.info("Starting local ingestion pipeline run...")
    await orchestrator.ingest_profile(
        profile_id=profile_id,
        cloudinary_url=pdf_dest,
        github_url=github_url,
        resume_bytes=file_bytes
    )
    
    # 4. Verify Local PDF Deletion
    logger.info("Verifying local PDF deletion...")
    if os.path.exists(pdf_dest):
        logger.error(f"❌ Failure! PDF file still exists at {pdf_dest}")
    else:
        logger.info(f"✅ Success! Local PDF file was successfully deleted at {pdf_dest}")

    # 5. Verify database records
    status_doc = await status_repo.get_by_profile_id(profile_id)
    if status_doc:
        logger.info(f"Pipeline status: {status_doc.status}, step: {status_doc.current_step}")
        if status_doc.status == "COMPLETED":
            logger.info("✅ Success! Pipeline state is COMPLETED.")
        else:
            logger.error(f"❌ Incomplete state: {status_doc.status}")
    else:
        logger.error("❌ No pipeline status found in DB.")

    close_connections()

if __name__ == "__main__":
    asyncio.run(main())
