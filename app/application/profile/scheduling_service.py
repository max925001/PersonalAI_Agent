import uuid
from datetime import datetime, timezone
from typing import List, Optional
from loguru import logger

from app.domain.profile.entities import Availability
from app.domain.profile.repository_interfaces import IAvailabilityRepository
from app.core.exceptions import ValidationException

class SchedulingService:
    """Service handling scheduling slots in MongoDB Atlas (never stored in Qdrant)."""

    def __init__(self, availability_repo: IAvailabilityRepository):
        self.availability_repo = availability_repo

    async def get_available_slots(self, profile_id: uuid.UUID) -> List[Availability]:
        """Retrieves all available (non-booked) slots for the candidate."""
        logger.info(f"Retrieves available slots for profile_id: {profile_id}")
        slots = await self.availability_repo.get_by_profile_id(profile_id)
        # Filter for non-booked and future slots
        now = datetime.now(timezone.utc)
        return [
            s for s in slots 
            if not s.is_booked and s.slot.replace(tzinfo=timezone.utc if s.slot.tzinfo is None else s.slot.tzinfo) > now
        ]

    async def book_interview_slot(
        self,
        profile_id: uuid.UUID,
        slot_time: datetime,
        booked_by_name: Optional[str] = None,
        booked_by_email: Optional[str] = None
    ) -> bool:
        """
        Books a specific interview slot. 
        Validates the slot exists and is not already booked.
        """
        logger.info(f"Booking request received for profile {profile_id} at {slot_time.isoformat()}")
        slots = await self.availability_repo.get_by_profile_id(profile_id)
        
        target_slot: Optional[Availability] = None
        for s in slots:
            # Normalize to timezone-aware comparisons
            s_time = s.slot.replace(tzinfo=timezone.utc if s.slot.tzinfo is None else s.slot.tzinfo)
            req_time = slot_time.replace(tzinfo=timezone.utc if slot_time.tzinfo is None else slot_time.tzinfo)
            
            if s_time == req_time:
                target_slot = s
                break
                
        if not target_slot:
            raise ValidationException("The requested interview slot is not available for this profile.")
            
        if target_slot.is_booked:
            raise ValidationException("This interview slot has already been booked.")
            
        target_slot.is_booked = True
        target_slot.booked_by_name = booked_by_name
        target_slot.booked_by_email = booked_by_email
        await self.availability_repo.save_all([target_slot])
        
        logger.info(f"Slot booked successfully: {slot_time.isoformat()} for profile {profile_id}")
        return True

    async def set_availability(self, profile_id: uuid.UUID, slots: List[datetime]) -> List[Availability]:
        """
        Overrides the profile's availability slots.
        Validates there are exactly 5 slots, no past slots, and no duplicates.
        """
        logger.info(f"Setting availability for profile {profile_id} with {len(slots)} slots")
        
        # 1. Validation logic
        if len(slots) != 5:
            raise ValidationException("Availability must consist of exactly 5 interview slots.")
            
        now = datetime.now(timezone.utc)
        normalized_slots = []
        for s in slots:
            s_aware = s.replace(tzinfo=timezone.utc if s.tzinfo is None else s.tzinfo)
            if s_aware < now:
                raise ValidationException("Cannot add availability slots in the past.")
            normalized_slots.append(s_aware)
            
        # Check duplicates
        if len(set(normalized_slots)) != len(normalized_slots):
            raise ValidationException("Availability slots must contain unique dates.")

        # 2. Clear old availability slots
        await self.availability_repo.delete_by_profile_id(profile_id)

        # 3. Create new slots
        availabilities = [
            Availability(profile_id=profile_id, slot=slot, is_booked=False)
            for slot in normalized_slots
        ]
        
        await self.availability_repo.save_all(availabilities)
        logger.info(f"Availability updated successfully with 5 slots for profile: {profile_id}")
        return availabilities
