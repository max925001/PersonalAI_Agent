import uuid
from typing import Optional
from app.domain.auth.entities import User
from app.domain.auth.value_objects import Email, PasswordHash
from app.domain.auth.repository_interfaces import IUserRepository
from app.infrastructure.persistence.mongodb.documents.user_document import UserDocument

class BeanieUserRepository(IUserRepository):
    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        doc = await UserDocument.get(user_id)
        return self._to_domain(doc) if doc else None

    async def get_by_email(self, email: Email) -> Optional[User]:
        doc = await UserDocument.find_one(UserDocument.email == email.value)
        return self._to_domain(doc) if doc else None

    async def save(self, user: User) -> User:
        # Check if exists to update, otherwise insert
        doc = await UserDocument.get(user.id)
        if not doc:
            doc = UserDocument(
                id=user.id,
                email=user.email.value,
                password_hash=user.password_hash.value,
                is_active=user.is_active,
                created_at=user.created_at
            )
        else:
            doc.email = user.email.value
            doc.password_hash = user.password_hash.value
            doc.is_active = user.is_active
            
        await doc.save()
        return user

    def _to_domain(self, doc: UserDocument) -> User:
        return User(
            id=doc.id,
            email=Email(doc.email),
            password_hash=PasswordHash(doc.password_hash),
            is_active=doc.is_active,
            created_at=doc.created_at
        )