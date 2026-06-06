import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, status, HTTPException
from pydantic import BaseModel, EmailStr, Field
from loguru import logger

from app.core.exceptions import ValidationException
from app.application.profile.scheduling_service import SchedulingService
from app.domain.profile.repository_interfaces import IProfileRepository
from app.infrastructure.web.dependencies import get_scheduling_service, get_profile_repository

router = APIRouter()

# ── Schemas ──────────────────────────────────────────────────────────────────

class SlotResponse(BaseModel):
    id: uuid.UUID
    slot: datetime
    is_booked: bool
    booked_by_name: Optional[str] = None
    booked_by_email: Optional[str] = None

    class Config:
        from_attributes = True

class BookSlotRequest(BaseModel):
    slot: datetime = Field(..., description="The ISO datetime of the slot to book")
    name: str = Field(..., min_length=1, max_length=100, description="Recruiter's name")
    email: EmailStr = Field(..., description="Recruiter's corporate email")

# ── Routes ───────────────────────────────────────────────────────────────────

@router.get("/slots", response_model=List[SlotResponse], status_code=status.HTTP_200_OK)
async def get_available_slots(
    profile_repo: IProfileRepository = Depends(get_profile_repository),
    scheduling_service: SchedulingService = Depends(get_scheduling_service)
) -> List[SlotResponse]:
    """
    Public endpoint for recruiters to view available interview slots.
    """
    logger.info("Recruiter requested available slots.")
    profile = await profile_repo.get_current()
    if not profile:
        logger.warning("No profile found when retrieving slots.")
        return []
        
    slots = await scheduling_service.get_available_slots(profile.id)
    return [
        SlotResponse(
            id=s.id,
            slot=s.slot,
            is_booked=s.is_booked,
            booked_by_name=s.booked_by_name,
            booked_by_email=s.booked_by_email
        )
        for s in slots
    ]

@router.post("/book", status_code=status.HTTP_200_OK)
async def book_slot(
    payload: BookSlotRequest,
    profile_repo: IProfileRepository = Depends(get_profile_repository),
    scheduling_service: SchedulingService = Depends(get_scheduling_service)
):
    """
    Public endpoint for recruiters to book a specific interview slot.
    """
    logger.info(f"Recruiter '{payload.name}' ({payload.email}) booking request for {payload.slot.isoformat()}")
    profile = await profile_repo.get_current()
    if not profile:
        raise ValidationException("Profile not found. Cannot book slot.")

    # Execute booking via service
    success = await scheduling_service.book_interview_slot(
        profile_id=profile.id,
        slot_time=payload.slot,
        booked_by_name=payload.name,
        booked_by_email=payload.email
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to book slot."
        )
        
    return {"message": "Success", "slot": payload.slot}
