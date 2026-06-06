import uuid
from typing import Optional
from app.domain.profile.entities import EmbeddingJob
from app.domain.profile.repository_interfaces import IEmbeddingJobRepository
from app.infrastructure.persistence.mongodb.documents.embedding_job_document import EmbeddingJobDocument

class BeanieEmbeddingJobRepository(IEmbeddingJobRepository):
    async def get_by_id(self, job_id: uuid.UUID) -> Optional[EmbeddingJob]:
        doc = await EmbeddingJobDocument.get(job_id)
        return self._to_domain(doc) if doc else None

    async def save(self, job: EmbeddingJob) -> EmbeddingJob:
        doc = await EmbeddingJobDocument.get(job.id)
        if not doc:
            doc = EmbeddingJobDocument(
                id=job.id,
                profile_id=job.profile_id,
                status=job.status,
                error_message=job.error_message,
                created_at=job.created_at,
                updated_at=job.updated_at
            )
        else:
            doc.status = job.status
            doc.error_message = job.error_message
            doc.updated_at = job.updated_at

        await doc.save()
        return job

    def _to_domain(self, doc: EmbeddingJobDocument) -> EmbeddingJob:
        return EmbeddingJob(
            id=doc.id,
            profile_id=doc.profile_id,
            status=doc.status,
            error_message=doc.error_message,
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )
