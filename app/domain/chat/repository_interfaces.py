from abc import ABC, abstractmethod
import uuid
from typing import List, Optional
from app.domain.chat.entities import Conversation, Message

class IConversationRepository(ABC):
    @abstractmethod
    async def get_by_session_id(self, session_id: uuid.UUID) -> Optional[Conversation]:
        """Retrieves a conversation by its unique session ID."""
        pass

    @abstractmethod
    async def save(self, conversation: Conversation) -> None:
        """Saves or updates a conversation session."""
        pass


class IMessageRepository(ABC):
    @abstractmethod
    async def get_recent_messages(self, session_id: uuid.UUID, limit: int) -> List[Message]:
        """Retrieves the last N messages for a conversation session ordered by timestamp."""
        pass

    @abstractmethod
    async def save(self, message: Message) -> None:
        """Saves a new chat message."""
        pass

    @abstractmethod
    async def delete_by_session_id(self, session_id: uuid.UUID) -> None:
        """Deletes all messages associated with a session ID."""
        pass
