from fastapi import APIRouter, Depends, status
import uuid
from loguru import logger

from app.application.chat.dtos import ChatRequest, ChatResponse, Citation
from app.application.agent.agent_use_case import AgentUseCase
from app.infrastructure.web.dependencies import get_agent_use_case

router = APIRouter()

@router.post("", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat(
    payload: ChatRequest,
    use_case: AgentUseCase = Depends(get_agent_use_case)
) -> ChatResponse:
    """
    Retrieves semantic RAG answers for candidate queries, maintaining conversation history.
    """
    logger.info("Chat API request received.")
    
    # 1. Resolve Session ID
    session_id_str = payload.session_id
    if not session_id_str:
        session_id_str = str(uuid.uuid4())
        logger.info(f"No session_id provided. Generated new session_id: {session_id_str}")
    else:
        # Validate UUID format. If not a valid UUID, generate a deterministic UUID based on the string
        try:
            uuid.UUID(session_id_str)
        except ValueError:
            deterministic_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, session_id_str)
            session_id_str = str(deterministic_uuid)
            logger.info(f"Non-UUID session_id provided. Converted deterministically to UUID: {session_id_str}")

    # 2. Execute RAG Chat Use Case
    result = await use_case.execute(
        session_id=session_id_str,
        message=payload.message
    )
    
    # 3. Format response DTO
    citations = [
        Citation(
            source_type=s["source_type"],
            source_id=s["source_id"],
            repository_name=s.get("repository_name")
        )
        for s in result["sources"]
    ]
    
    return ChatResponse(
        answer=result["response"],
        sources=citations,
        confidence=result["confidence_score"],
        elapsed_time_seconds=result["elapsed_time_seconds"]
    )
