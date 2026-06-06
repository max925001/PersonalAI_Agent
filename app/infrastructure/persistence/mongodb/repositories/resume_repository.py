import uuid
from typing import Optional
from app.domain.profile.entities import Resume
from app.domain.profile.repository_interfaces import IResumeRepository
from app.infrastructure.persistence.mongodb.documents.resume_document import ResumeDocument

class BeanieResumeRepository(IResumeRepository):
    async def get_by_id(self, resume_id: uuid.UUID) -> Optional[Resume]:
        doc = await ResumeDocument.get(resume_id)
        return self._to_domain(doc) if doc else None

    async def get_by_profile_id(self, profile_id: uuid.UUID) -> Optional[Resume]:
        doc = await ResumeDocument.find_one(ResumeDocument.profile_id == profile_id)
        return self._to_domain(doc) if doc else None

    async def save(self, resume: Resume) -> Resume:
        doc = await ResumeDocument.get(resume.id)
        if not doc:
            doc = ResumeDocument(
                id=resume.id,
                profile_id=resume.profile_id,
                cloudinary_url=resume.cloudinary_url,
                cloudinary_public_id=resume.cloudinary_public_id,
                content_hash=resume.content_hash,
                extracted_text=resume.extracted_text,
                created_at=resume.created_at,
                updated_at=resume.updated_at
            )
        else:
            doc.cloudinary_url = resume.cloudinary_url
            doc.cloudinary_public_id = resume.cloudinary_public_id
            doc.content_hash = resume.content_hash
            doc.extracted_text = resume.extracted_text
            doc.updated_at = resume.updated_at
            
        await doc.save()
        return resume

    def _to_domain(self, doc: ResumeDocument) -> Resume:
        return Resume(
            id=doc.id,
            profile_id=doc.profile_id,
            cloudinary_url=doc.cloudinary_url,
            cloudinary_public_id=doc.cloudinary_public_id,
            content_hash=doc.content_hash,
            extracted_text=doc.extracted_text,
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )
