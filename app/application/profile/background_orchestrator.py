import uuid
from datetime import datetime, timezone
from typing import Optional
from loguru import logger

from app.core.exceptions import AppException
from app.domain.profile.entities import ProcessingStatus, EmbeddingJob
from app.domain.profile.repository_interfaces import (
    IProfileRepository, IResumeRepository, IProcessingStatusRepository, IEmbeddingJobRepository
)
from app.application.profile.resume_processor import ResumeProcessor
from app.application.profile.github_service import GitHubService
from app.application.profile.repository_sync_service import RepositorySyncService
from app.application.profile.knowledge_document_service import KnowledgeDocumentService
from app.application.profile.chunking_service import ChunkingService
from app.application.profile.embedding_service import EmbeddingService
from app.application.profile.qdrant_service import QdrantService
from app.application.interfaces.embedding_port import IEmbeddingPort

class BackgroundJobOrchestrator:
    """Orchestrates the asynchronous Profile Ingestion Pipeline tasks."""

    def __init__(
        self,
        profile_repo: IProfileRepository,
        resume_repo: IResumeRepository,
        status_repo: IProcessingStatusRepository,
        embedding_job_repo: IEmbeddingJobRepository,
        resume_processor: ResumeProcessor,
        github_service: GitHubService,
        sync_service: RepositorySyncService,
        knowledge_service: KnowledgeDocumentService,
        chunking_service: ChunkingService,
        embedding_service: EmbeddingService,
        qdrant_service: QdrantService,
        embedding_port: IEmbeddingPort
    ):
        self.profile_repo = profile_repo
        self.resume_repo = resume_repo
        self.status_repo = status_repo
        self.embedding_job_repo = embedding_job_repo
        self.resume_processor = resume_processor
        self.github_service = github_service
        self.sync_service = sync_service
        self.knowledge_service = knowledge_service
        self.chunking_service = chunking_service
        self.embedding_service = embedding_service
        self.qdrant_service = qdrant_service
        self.embedding_port = embedding_port

    async def _update_status(
        self, 
        profile_id: uuid.UUID, 
        step: str, 
        progress: float, 
        status: str, 
        error: Optional[str] = None
    ) -> None:
        logger.info(f"Pipeline status update: Profile {profile_id} -> Step: {step}, Progress: {progress}%, Status: {status}")
        
        proc_status = await self.status_repo.get_by_profile_id(profile_id)
        if not proc_status:
            proc_status = ProcessingStatus(
                profile_id=profile_id,
                current_step=step,
                progress=progress,
                status=status,
                error_message=error
            )
        else:
            proc_status.current_step = step
            proc_status.progress = progress
            proc_status.status = status
            proc_status.error_message = error
            proc_status.last_updated = datetime.now(timezone.utc)
            
        await self.status_repo.save(proc_status)

    async def ingest_profile(self, profile_id: uuid.UUID, cloudinary_url: str, github_url: str, resume_bytes: Optional[bytes] = None) -> None:
        """
        Runs the profile ingestion flow.
        Updates processing status asynchronously at each milestone.
        """
        logger.info(f"Starting Background Ingestion Pipeline for profile_id: {profile_id}")
        start_time = datetime.now()
        
        try:
            # 1. Update status to PROCESSING / RESUME_PROCESSING
            await self._update_status(profile_id, "RESUME_PROCESSING", 10.0, "PROCESSING")
            
            # Fetch profile
            profile = await self.profile_repo.get_by_id(profile_id)
            if not profile:
                raise ValueError(f"Profile {profile_id} not found in database.")

            # 2. Extract and Normalize Resume
            if resume_bytes:
                logger.info("Using uploaded resume bytes directly, skipping download.")
                extracted_text = self.resume_processor.extract_text_from_pdf(resume_bytes)
                normalized_text = self.resume_processor.normalize_text(extracted_text)
                resume_hash = self.resume_processor.generate_sha256_hash(normalized_text)
                
                existing_resume = await self.resume_repo.get_by_profile_id(profile_id)
                resume_changed = True
                if existing_resume and existing_resume.content_hash == resume_hash:
                    logger.info(f"Resume content hash ({resume_hash}) is unchanged. Skipping vector regeneration.")
                    resume_changed = False
                    extracted_text = existing_resume.extracted_text or normalized_text
                else:
                    extracted_text = normalized_text
            else:
                extracted_text, resume_hash, resume_changed = await self.resume_processor.process_resume(
                    profile_id=profile_id,
                    cloudinary_url=cloudinary_url
                )
            
            # Save or update Resume record
            resume = await self.resume_repo.get_by_profile_id(profile_id)
            if not resume:
                from app.domain.profile.entities import Resume as DomainResume
                resume = DomainResume(
                    profile_id=profile_id,
                    cloudinary_url=cloudinary_url,
                    cloudinary_public_id=cloudinary_url.split('/')[-1].split('.')[0],
                    content_hash=resume_hash,
                    extracted_text=extracted_text
                )
                await self.resume_repo.save(resume)
            else:
                resume.cloudinary_url = cloudinary_url
                resume.cloudinary_public_id = cloudinary_url.split('/')[-1].split('.')[0]
                resume.content_hash = resume_hash
                resume.extracted_text = extracted_text
                await self.resume_repo.save(resume)

            # 3. GitHub Ingestion and Sync
            await self._update_status(profile_id, "GITHUB_SYNC", 40.0, "PROCESSING")
            
            # Extract username from GitHub URL
            from app.domain.profile.value_objects import GitHubUrl
            github_vo = GitHubUrl(github_url)
            username = github_vo.username
            
            repos_data = await self.github_service.get_repositories_data(username)
            repositories, repos_changed = await self.sync_repositories_with_db(profile_id, repos_data)

            # 4. Compile Knowledge Documents
            await self._update_status(profile_id, "KNOWLEDGE_DOC_COMPILE", 65.0, "PROCESSING")
            
            knowledge_docs = await self.knowledge_service.generate_knowledge_documents(
                profile=profile,
                resume=resume,
                repositories=repositories
            )

            # Optimization Check: If resume and repositories have not changed, SKIP embeddings & Qdrant syncing
            if not resume_changed and not repos_changed:
                logger.info("Optimization triggered: No changes detected in Resume or GitHub Repositories. Skipping vector database sync.")
                await self._update_status(profile_id, "COMPLETED", 100.0, "COMPLETED")
                logger.info(f"Pipeline finished. Time elapsed: {datetime.now() - start_time}")
                return

            # 5. Document Chunking
            await self._update_status(profile_id, "CHUNKING", 75.0, "PROCESSING")
            chunks = self.chunking_service.chunk_documents(knowledge_docs)

            if not chunks:
                logger.warning("No knowledge base chunks created. Completing task.")
                await self._update_status(profile_id, "COMPLETED", 100.0, "COMPLETED")
                return

            # 6. Generate Embeddings (batch request)
            await self._update_status(profile_id, "EMBEDDINGS", 85.0, "PROCESSING")
            
            # Create a record for this embedding job
            emb_job = EmbeddingJob(profile_id=profile_id, status="PROCESSING")
            await self.embedding_job_repo.save(emb_job)
            
            try:
                # Query Qdrant for existing vectors to bypass Gemini API rate limit consumption
                point_ids = []
                chunk_by_point_id = {}
                for chunk in chunks:
                    pt_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk["hash"]))
                    point_ids.append(pt_id)
                    chunk_by_point_id[pt_id] = chunk
                
                logger.info(f"Checking Qdrant for cached vectors for {len(chunks)} chunks...")
                existing_vectors = await self.qdrant_service.get_existing_vectors(point_ids)
                
                cached_count = 0
                for pt_id, vector in existing_vectors.items():
                    if pt_id in chunk_by_point_id:
                        chunk_by_point_id[pt_id]["vector"] = vector
                        cached_count += 1
                
                logger.info(f"Found {cached_count}/{len(chunks)} vectors cached in Qdrant.")
                
                embedded_chunks = await self.embedding_service.embed_chunks(chunks)
                emb_job.status = "COMPLETED"
                await self.embedding_job_repo.save(emb_job)
            except Exception as emb_err:
                emb_job.status = "FAILED"
                emb_job.error_message = str(emb_err)
                await self.embedding_job_repo.save(emb_job)
                raise emb_err

            # 7. Qdrant Bulk Upsert
            await self._update_status(profile_id, "QDRANT_UPSERT", 95.0, "PROCESSING")
            
            # Ensure the collection and its payload indexes exist before calling clear or upsert
            await self.qdrant_service.ensure_collection_ready(self.embedding_port.dimension)
            
            # Clear previous vectors to prevent orphans/duplicates
            await self.qdrant_service.clear_profile_vectors(str(profile_id))
            
            # Save new ones
            await self.qdrant_service.save_chunks_to_vector_store(
                chunks=embedded_chunks,
                profile_id=str(profile_id),
                vector_size=self.embedding_port.dimension
            )

            # 8. Complete Pipeline
            await self._update_status(profile_id, "COMPLETED", 100.0, "COMPLETED")
            
            duration = datetime.now() - start_time
            logger.info(f"Ingestion Pipeline completed successfully for profile_id {profile_id} in {duration.total_seconds()}s.")
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Ingestion Pipeline failed for profile_id {profile_id}: {error_msg}")
            
            status = "FAILED"
            # Attempt to record error state in database
            try:
                await self._update_status(profile_id, "FAILED", 100.0, status, error=error_msg)
            except Exception as db_err:
                logger.critical(f"Failed to save pipeline error state to MongoDB: {str(db_err)}")
        finally:
            self._delete_local_pdf(profile_id)

    def _delete_local_pdf(self, profile_id: uuid.UUID) -> None:
        import os
        local_pdf_path = f"uploads/{profile_id}.pdf"
        if os.path.exists(local_pdf_path):
            try:
                os.remove(local_pdf_path)
                logger.info(f"Deleted temporary local PDF: {local_pdf_path}")
            except Exception as del_err:
                logger.warning(f"Failed to delete temporary local PDF {local_pdf_path}: {str(del_err)}")

    async def sync_repositories_with_db(self, profile_id: uuid.UUID, repos_data: list) -> tuple:
        """Helper to call repository sync service."""
        return await self.sync_service.sync_repositories(profile_id, repos_data)
