import uuid
from typing import Optional
from app.domain.chat.entities import Conversation
from app.domain.chat.repository_interfaces import IConversationRepository
from app.infrastructure.persistence.mongodb.documents.conversation_document import ConversationDocument

class BeanieConversationRepository(IConversationRepository):
    async def get_by_session_id(self, session_id: uuid.UUID) -> Optional[Conversation]:
        doc = await ConversationDocument.find_one(ConversationDocument.session_id == session_id)
        if not doc:
            return None
        return Conversation(
            id=doc.id,
            session_id=doc.session_id,
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )

    async def save(self, conversation: Conversation) -> None:
        doc = await ConversationDocument.find_one(ConversationDocument.session_id == conversation.session_id)
        if not doc:
            doc = ConversationDocument(
                id=conversation.id,
                session_id=conversation.session_id,
                created_at=conversation.created_at,
                updated_at=conversation.updated_at
            )
            await doc.insert()
        else:
            doc.updated_at = conversation.updated_at
            await doc.save()
