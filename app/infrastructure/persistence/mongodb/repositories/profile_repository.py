import uuid
from typing import Optional
from app.domain.profile.entities import Profile
from app.domain.profile.repository_interfaces import IProfileRepository
from app.infrastructure.persistence.mongodb.documents.profile_document import ProfileDocument

class BeanieProfileRepository(IProfileRepository):
    async def get_by_id(self, profile_id: uuid.UUID) -> Optional[Profile]:
        doc = await ProfileDocument.get(profile_id)
        return self._to_domain(doc) if doc else None

    async def save(self, profile: Profile) -> Profile:
        doc = await ProfileDocument.get(profile.id)
        if not doc:
            doc = ProfileDocument(
                id=profile.id,
                github_url=profile.github_url,
                additional_information=profile.additional_information,
                created_at=profile.created_at,
                updated_at=profile.updated_at
            )
        else:
            doc.github_url = profile.github_url
            doc.additional_information = profile.additional_information
            doc.updated_at = profile.updated_at
        
        await doc.save()
        return profile

    async def get_current(self) -> Optional[Profile]:
        # Since this platform represents ONE candidate only, return the first one
        doc = await ProfileDocument.find_one()
        return self._to_domain(doc) if doc else None

    def _to_domain(self, doc: ProfileDocument) -> Profile:
        return Profile(
            id=doc.id,
            github_url=doc.github_url,
            additional_information=doc.additional_information,
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )
