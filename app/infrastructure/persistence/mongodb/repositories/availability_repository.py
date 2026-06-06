import uuid
from typing import List
from app.domain.profile.entities import Availability
from app.domain.profile.repository_interfaces import IAvailabilityRepository
from app.infrastructure.persistence.mongodb.documents.availability_document import AvailabilityDocument

class BeanieAvailabilityRepository(IAvailabilityRepository):
    async def get_by_profile_id(self, profile_id: uuid.UUID) -> List[Availability]:
        docs = await AvailabilityDocument.find(AvailabilityDocument.profile_id == profile_id).to_list()
        return [self._to_domain(doc) for doc in docs]

    async def save_all(self, availabilities: List[Availability]) -> List[Availability]:
        for availability in availabilities:
            doc = await AvailabilityDocument.get(availability.id)
            if not doc:
                doc = AvailabilityDocument(
                    id=availability.id,
                    profile_id=availability.profile_id,
                    slot=availability.slot,
                    is_booked=availability.is_booked,
                    booked_by_name=availability.booked_by_name,
                    booked_by_email=availability.booked_by_email,
                    created_at=availability.created_at
                )
            else:
                doc.slot = availability.slot
                doc.is_booked = availability.is_booked
                doc.booked_by_name = availability.booked_by_name
                doc.booked_by_email = availability.booked_by_email
            await doc.save()
        return availabilities

    async def delete_by_profile_id(self, profile_id: uuid.UUID) -> None:
        await AvailabilityDocument.find(AvailabilityDocument.profile_id == profile_id).delete()

    def _to_domain(self, doc: AvailabilityDocument) -> Availability:
        return Availability(
            id=doc.id,
            profile_id=doc.profile_id,
            slot=doc.slot,
            is_booked=doc.is_booked,
            booked_by_name=doc.booked_by_name,
            booked_by_email=doc.booked_by_email,
            created_at=doc.created_at
        )
