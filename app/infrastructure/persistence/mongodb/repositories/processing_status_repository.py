import uuid
from typing import Optional
from app.domain.profile.entities import ProcessingStatus
from app.domain.profile.repository_interfaces import IProcessingStatusRepository
from app.infrastructure.persistence.mongodb.documents.processing_status_document import ProcessingStatusDocument

class BeanieProcessingStatusRepository(IProcessingStatusRepository):
    async def get_by_profile_id(self, profile_id: uuid.UUID) -> Optional[ProcessingStatus]:
        doc = await ProcessingStatusDocument.find_one(ProcessingStatusDocument.profile_id == profile_id)
        return self._to_domain(doc) if doc else None

    async def save(self, status: ProcessingStatus) -> ProcessingStatus:
        doc = await ProcessingStatusDocument.find_one(ProcessingStatusDocument.profile_id == status.profile_id)
        if not doc:
            doc = ProcessingStatusDocument(
                id=status.id,
                profile_id=status.profile_id,
                current_step=status.current_step,
                progress=status.progress,
                status=status.status,
                error_message=status.error_message,
                last_updated=status.last_updated
            )
        else:
            doc.current_step = status.current_step
            doc.progress = status.progress
            doc.status = status.status
            doc.error_message = status.error_message
            doc.last_updated = status.last_updated

        await doc.save()
        return status

    def _to_domain(self, doc: ProcessingStatusDocument) -> ProcessingStatus:
        return ProcessingStatus(
            id=doc.id,
            profile_id=doc.profile_id,
            current_step=doc.current_step,
            progress=doc.progress,
            status=doc.status,
            error_message=doc.error_message,
            last_updated=doc.last_updated
        )
