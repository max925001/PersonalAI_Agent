import uuid
from abc import ABC, abstractmethod
from typing import Optional
from app.domain.auth.entities import User, RefreshTokenSession
from app.domain.auth.value_objects import Email

class IUserRepository(ABC):
    @abstractmethod
    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        pass

    @abstractmethod
    async def get_by_email(self, email: Email) -> Optional[User]:
        pass

    @abstractmethod
    async def save(self, user: User) -> User:
        pass


class IRefreshTokenRepository(ABC):
    @abstractmethod
    async def get_by_hash(self, token_hash: str) -> Optional[RefreshTokenSession]:
        pass

    @abstractmethod
    async def save(self, session: RefreshTokenSession) -> RefreshTokenSession:
        pass

    @abstractmethod
    async def revoke_all_by_user(self, user_id: uuid.UUID) -> None:
        pass