import uuid
from typing import List
from app.domain.chat.entities import Message
from app.domain.chat.repository_interfaces import IMessageRepository
from app.infrastructure.persistence.mongodb.documents.message_document import MessageDocument

class BeanieMessageRepository(IMessageRepository):
    async def get_recent_messages(self, session_id: uuid.UUID, limit: int) -> List[Message]:
        # Sort descending by timestamp, take limit, then reverse to return chronological order
        docs = await MessageDocument.find(
            MessageDocument.session_id == session_id
        ).sort("-timestamp").limit(limit).to_list()
        
        # Reverse to ensure chronological order
        docs.reverse()
        
        return [
            Message(
                id=doc.id,
                session_id=doc.session_id,
                role=doc.role,
                content=doc.content,
                timestamp=doc.timestamp
            )
            for doc in docs
        ]

    async def save(self, message: Message) -> None:
        doc = MessageDocument(
            id=message.id,
            session_id=message.session_id,
            role=message.role,
            content=message.content,
            timestamp=message.timestamp
        )
        await doc.insert()

    async def delete_by_session_id(self, session_id: uuid.UUID) -> None:
        await MessageDocument.find(MessageDocument.session_id == session_id).delete()
