from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator, HttpUrl
from typing import List, Optional
import uuid

class AvailabilityValidationModel(BaseModel):
    """Pydantic model for validating the 5 availability slots."""
    slots: List[datetime]

    @field_validator("slots")
    @classmethod
    def validate_slots(cls, v: List[datetime]) -> List[datetime]:
        if len(v) != 5:
            raise ValueError("Exactly 5 interview slots must be provided.")
        
        now = datetime.now(timezone.utc)
        normalized = []
        for dt in v:
            # Convert timezone-naive datetimes to timezone-aware UTC
            dt_utc = dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)
            
            if dt_utc < now:
                raise ValueError(f"Availability slot {dt.isoformat()} cannot be in the past.")
            normalized.append(dt_utc)

        # Check for duplicate dates
        if len(set(normalized)) != len(normalized):
            raise ValueError("Availability slots must contain unique dates.")

        return normalized


class ProfileResponse(BaseModel):
    """API Response DTO for profile creation."""
    id: uuid.UUID
    github_url: str
    additional_information: Optional[str] = None
    created_at: datetime
    status: str = "PENDING"


class ProcessingStatusResponse(BaseModel):
    """API Response DTO for pipeline execution progress tracking."""
    profile_id: uuid.UUID
    current_step: str
    progress: float  # Percentage (0.0 to 100.0)
    status: str      # PENDING, PROCESSING, COMPLETED, FAILED
    error_message: Optional[str] = None
    last_updated: datetime
