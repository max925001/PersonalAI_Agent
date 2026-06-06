import uuid
from typing import Optional
from app.domain.auth.entities import RefreshTokenSession
from app.domain.auth.repository_interfaces import IRefreshTokenRepository
from app.infrastructure.persistence.mongodb.documents.token_document import RefreshTokenDocument

class BeanieRefreshTokenRepository(IRefreshTokenRepository):
    async def get_by_hash(self, token_hash: str) -> Optional[RefreshTokenSession]:
        doc = await RefreshTokenDocument.find_one(RefreshTokenDocument.token_hash == token_hash)
        return self._to_domain(doc) if doc else None

    async def save(self, session: RefreshTokenSession) -> RefreshTokenSession:
        doc = await RefreshTokenDocument.get(session.id)
        if not doc:
            doc = RefreshTokenDocument(
                id=session.id,
                user_id=session.user_id,
                token_hash=session.token_hash,
                expires_at=session.expires_at,
                revoked=session.revoked,
                created_at=session.created_at
            )
        else:
            doc.revoked = session.revoked
            doc.expires_at = session.expires_at
            
        await doc.save()
        return session

    async def revoke_all_by_user(self, user_id: uuid.UUID) -> None:
        await RefreshTokenDocument.find(
            RefreshTokenDocument.user_id == user_id
        ).set({RefreshTokenDocument.revoked: True})

    def _to_domain(self, doc: RefreshTokenDocument) -> RefreshTokenSession:
        return RefreshTokenSession(
            id=doc.id,
            user_id=doc.user_id,
            token_hash=doc.token_hash,
            expires_at=doc.expires_at,
            revoked=doc.revoked,
            created_at=doc.created_at
        )