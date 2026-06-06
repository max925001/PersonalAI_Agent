import uuid
from typing import List
from app.domain.profile.entities import KnowledgeDocument
from app.domain.profile.repository_interfaces import IKnowledgeDocumentRepository
from app.infrastructure.persistence.mongodb.documents.knowledge_document import KnowledgeDocumentDocument

class BeanieKnowledgeDocumentRepository(IKnowledgeDocumentRepository):
    async def get_by_profile_id(self, profile_id: uuid.UUID) -> List[KnowledgeDocument]:
        docs = await KnowledgeDocumentDocument.find(KnowledgeDocumentDocument.profile_id == profile_id).to_list()
        return [self._to_domain(doc) for doc in docs]

    async def save(self, doc: KnowledgeDocument) -> KnowledgeDocument:
        db_doc = await KnowledgeDocumentDocument.get(doc.id)
        if not db_doc:
            db_doc = KnowledgeDocumentDocument(
                id=doc.id,
                profile_id=doc.profile_id,
                source_type=doc.source_type,
                source_id=doc.source_id,
                title=doc.title,
                content=doc.content,
                metadata=doc.metadata,
                created_at=doc.created_at
            )
        else:
            db_doc.source_type = doc.source_type
            db_doc.source_id = doc.source_id
            db_doc.title = doc.title
            db_doc.content = doc.content
            db_doc.metadata = doc.metadata

        await db_doc.save()
        return doc

    async def delete_by_profile_id(self, profile_id: uuid.UUID) -> None:
        await KnowledgeDocumentDocument.find(KnowledgeDocumentDocument.profile_id == profile_id).delete()

    def _to_domain(self, doc: KnowledgeDocumentDocument) -> KnowledgeDocument:
        return KnowledgeDocument(
            id=doc.id,
            profile_id=doc.profile_id,
            source_type=doc.source_type,
            source_id=doc.source_id,
            title=doc.title,
            content=doc.content,
            metadata=doc.metadata,
            created_at=doc.created_at
        )
