import uuid
from typing import List, Dict, Any
from loguru import logger
from app.domain.chat.entities import Conversation, Message
from app.domain.chat.repository_interfaces import IConversationRepository, IMessageRepository

class MemoryService:
    """Service responsible for loading and saving conversation logs using sliding memory windows."""

    def __init__(self, conversation_repo: IConversationRepository, message_repo: IMessageRepository):
        self.conversation_repo = conversation_repo
        self.message_repo = message_repo

    async def get_or_create_conversation(self, session_id: uuid.UUID) -> Conversation:
        conversation = await self.conversation_repo.get_by_session_id(session_id)
        if not conversation:
            logger.info(f"Creating new conversation session in DB: {session_id}")
            conversation = Conversation(session_id=session_id)
            await self.conversation_repo.save(conversation)
        return conversation

    async def load_chat_history(self, session_id: uuid.UUID, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieves the recent conversation history in a list of dicts: [{'role': str, 'content': str}]."""
        # Ensure conversation exists
        await self.get_or_create_conversation(session_id)
        
        messages = await self.message_repo.get_recent_messages(session_id, limit)
        return [
            {"role": m.role, "content": m.content, "timestamp": m.timestamp.isoformat()}
            for m in messages
        ]

    async def add_message(self, session_id: uuid.UUID, role: str, content: str) -> None:
        """Saves an individual message to the database and updates the conversation update timestamp."""
        # Ensure conversation exists
        conversation = await self.get_or_create_conversation(session_id)
        
        # Save message
        message = Message(session_id=session_id, role=role, content=content)
        await self.message_repo.save(message)
        
        # Touch conversation updated_at
        from datetime import datetime, timezone
        conversation.updated_at = datetime.now(timezone.utc)
        await self.conversation_repo.save(conversation)
        logger.info(f"Added '{role}' message to session {session_id}")

    async def save_interaction(self, session_id: uuid.UUID, user_content: str, assistant_content: str) -> None:
        """Saves both user and assistant messages, and updates conversation updated_at in one workflow."""
        import asyncio
        from datetime import datetime, timezone
        
        # Ensure conversation exists
        conversation = await self.get_or_create_conversation(session_id)
        
        now = datetime.now(timezone.utc)
        
        user_msg = Message(session_id=session_id, role="user", content=user_content, timestamp=now)
        ast_msg = Message(session_id=session_id, role="assistant", content=assistant_content or "", timestamp=now)
        
        # Run saves in parallel
        await asyncio.gather(
            self.message_repo.save(user_msg),
            self.message_repo.save(ast_msg),
            return_exceptions=True
        )
        
        # Touch conversation updated_at
        conversation.updated_at = now
        await self.conversation_repo.save(conversation)
        logger.info(f"Saved user and assistant interaction for session {session_id}")
