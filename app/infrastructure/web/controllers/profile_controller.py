from datetime import datetime, timezone
import json
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, File, UploadFile, Form, status, BackgroundTasks
from loguru import logger

from app.core.exceptions import ValidationException
from app.domain.auth.entities import User
from app.infrastructure.web.dependencies import (
    get_current_user, get_profile_repository, get_resume_repository,
    get_availability_repository, get_storage_port, get_background_orchestrator,
    get_processing_status_repository, get_scheduling_service
)
from app.domain.profile.repository_interfaces import (
    IProfileRepository, IResumeRepository, IAvailabilityRepository, IProcessingStatusRepository
)
from app.application.interfaces.storage_port import IStoragePort
from app.application.profile.background_orchestrator import BackgroundJobOrchestrator
from app.application.profile.scheduling_service import SchedulingService
from app.application.profile.dtos import ProfileResponse, ProcessingStatusResponse, AvailabilityValidationModel
from app.domain.profile.value_objects import GitHubUrl
from app.domain.profile.entities import Profile as DomainProfile

router = APIRouter()

@router.post("/profile", response_model=ProfileResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_profile(
    background_tasks: BackgroundTasks,
    resume_file: UploadFile = File(...),
    github_url: str = Form(...),
    additional_information: Optional[str] = Form(None),
    availability: str = Form(...),  # Expect JSON list of datetime strings
    current_user: User = Depends(get_current_user),
    profile_repo: IProfileRepository = Depends(get_profile_repository),
    resume_repo: IResumeRepository = Depends(get_resume_repository),
    availability_repo: IAvailabilityRepository = Depends(get_availability_repository),
    status_repo: IProcessingStatusRepository = Depends(get_processing_status_repository),
    storage_port: IStoragePort = Depends(get_storage_port),
    orchestrator: BackgroundJobOrchestrator = Depends(get_background_orchestrator),
    scheduling_service: SchedulingService = Depends(get_scheduling_service)
):
    """
    Creates a new candidate profile.
    Uploads the resume PDF to Cloudinary and initiates the pipeline processing in the background.
    """
    logger.info(f"Admin '{current_user.email.value}' initiated profile creation.")

    # 1. Validate Resume PDF File
    if resume_file.content_type != "application/pdf":
        raise ValidationException("Only PDF resumes are allowed.")
        
    # Read file size (limit to 10 MB)
    file_bytes = await resume_file.read()
    max_size = 10 * 1024 * 1024  # 10MB
    if len(file_bytes) > max_size:
        raise ValidationException("Resume file size exceeds maximum limit of 10 MB.")
    
    # 2. Validate GitHub URL
    try:
        github_vo = GitHubUrl(github_url)
    except ValueError as e:
        raise ValidationException(str(e))

    # 3. Validate Availability Slots
    logger.info(f"Received raw availability string: {availability}")
    try:
        sanitized = availability.strip()
        # Check if the input is a plain comma-separated list of datetime strings
        if not sanitized.startswith("["):
            # Split by comma and strip quotes and whitespace
            slots_data = [item.strip().strip("'").strip('"') for item in sanitized.split(",") if item.strip()]
        else:
            if sanitized.endswith("]"):
                sanitized = sanitized.replace("'", '"')
            slots_data = json.loads(sanitized)
    except Exception as e:
        logger.warning(f"Failed to parse availability string: '{availability}'. Error: {str(e)}")
        raise ValidationException("Availability must be a valid JSON array or comma-separated list of ISO datetime strings.")

    try:
        # Validate through Pydantic DTO
        validated_availability = AvailabilityValidationModel(slots=slots_data)
    except Exception as e:
        raise ValidationException(str(e))

    # 4. Additional Information Length Check
    if additional_information and len(additional_information) > 5000:
        raise ValidationException("Additional information text length exceeds 5000 characters limit.")

    # 5. Create Profile Entity first to generate its unique UUID
    profile = DomainProfile(
        github_url=github_vo.value,
        additional_information=additional_information
    )
    await profile_repo.save(profile)

    # 6. Save Resume PDF Locally on the server
    import os
    logger.info("Saving resume PDF file locally on server...")
    os.makedirs("uploads", exist_ok=True)
    pdf_path = f"uploads/{profile.id}.pdf"
    try:
        with open(pdf_path, "wb") as f:
            f.write(file_bytes)
        logger.info(f"Resume saved locally at: {pdf_path}")
    except Exception as e:
        logger.error(f"Failed to save local PDF file: {str(e)}")
        raise ValidationException(f"Failed to save local resume file: {str(e)}")

    cloudinary_url = pdf_path
    cloudinary_pub_id = f"local_{profile.id}"

    # 7. Create Availability Slots (solely in MongoDB)
    await scheduling_service.set_availability(profile.id, validated_availability.slots)

    # 8. Set initial pending status
    from app.domain.profile.entities import ProcessingStatus
    initial_status = ProcessingStatus(
        profile_id=profile.id,
        current_step="PROFILE_CREATED",
        progress=0.0,
        status="PENDING",
        error_message=None
    )
    await status_repo.save(initial_status)

    # 9. Trigger background job
    background_tasks.add_task(
        orchestrator.ingest_profile,
        profile_id=profile.id,
        cloudinary_url=cloudinary_url,
        github_url=github_vo.value,
        resume_bytes=file_bytes
    )

    return ProfileResponse(
        id=profile.id,
        github_url=profile.github_url,
        additional_information=profile.additional_information,
        created_at=profile.created_at,
        status="PENDING"
    )

@router.get("/profile/status", response_model=ProcessingStatusResponse)
async def get_profile_status(
    profile_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    status_repo: IProcessingStatusRepository = Depends(get_processing_status_repository)
):
    """
    Retrieves the ingestion pipeline execution status for the given profile ID.
    """
    logger.info(f"Retrieving ingestion status for profile {profile_id}")
    status_data = await status_repo.get_by_profile_id(profile_id)
    if not status_data:
        raise ValidationException("No processing history found for the requested profile ID.")
        
    return ProcessingStatusResponse(
        profile_id=status_data.profile_id,
        current_step=status_data.current_step,
        progress=status_data.progress,
        status=status_data.status,
        error_message=status_data.error_message,
        last_updated=status_data.last_updated
    )
