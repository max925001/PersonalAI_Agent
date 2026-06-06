from datetime import datetime
import uuid
from typing import Optional
from loguru import logger
from app.infrastructure.persistence.mongodb.documents.call_session_document import CallSessionDocument

class CallSessionService:
    """Service managing Twilio voice call session lifecycle and states in MongoDB Atlas."""

    async def create_session(self, call_sid: str, from_number: str, to_number: str) -> CallSessionDocument:
        """Creates a new CallSession in MongoDB with a unique conversation_id."""
        logger.info(f"Creating call session for CallSid: {call_sid}")
        
        # Check if session already exists
        existing = await self.get_session_by_sid(call_sid)
        if existing:
            logger.info(f"Call session already exists for CallSid: {call_sid}. Returning existing session.")
            return existing
            
        # Re-use conversation_id to link with ChatMemory
        conversation_id = uuid.uuid4()
        
        session = CallSessionDocument(
            call_sid=call_sid,
            from_number=from_number,
            to_number=to_number,
            state="CALL_RECEIVED",
            conversation_id=conversation_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        await session.save()
        logger.info(f"Call session saved successfully. Conversation ID: {conversation_id}")
        return session

    async def get_session_by_sid(self, call_sid: str) -> Optional[CallSessionDocument]:
        """Retrieves a call session by its Twilio Call SID."""
        return await CallSessionDocument.find_one(CallSessionDocument.call_sid == call_sid)

    async def update_session_state(self, call_sid: str, new_state: str) -> Optional[CallSessionDocument]:
        """Transitions call session state and saves it."""
        session = await self.get_session_by_sid(call_sid)
        if not session:
            logger.warning(f"Could not find call session {call_sid} to update state to {new_state}")
            return None
            
        logger.info(f"Transitioning CallSid {call_sid} state: {session.state} -> {new_state}")
        session.state = new_state
        session.updated_at = datetime.utcnow()
        await session.save()
        return session
