import uuid
from datetime import datetime, timezone
from typing import Optional
from app.domain.auth.value_objects import Email, PasswordHash

class User:
    """Domain representation of a user (Shivam Admin or visitors)."""
    def __init__(
        self,
        email: Email,
        password_hash: PasswordHash,
        is_active: bool = True,
        id: Optional[uuid.UUID] = None,
        created_at: Optional[datetime] = None
    ):
        self.id = id or uuid.uuid4()
        self.email = email
        self.password_hash = password_hash
        self.is_active = is_active
        self.created_at = created_at or datetime.now(timezone.utc)


class RefreshTokenSession:
    """Domain representation of an active refresh token session."""
    def __init__(
        self,
        user_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
        revoked: bool = False,
        id: Optional[uuid.UUID] = None,
        created_at: Optional[datetime] = None
    ):
        self.id = id or uuid.uuid4()
        self.user_id = user_id
        self.token_hash = token_hash
        self.expires_at = expires_at
        self.revoked = revoked
        self.created_at = created_at or datetime.now(timezone.utc)

    @property
    def is_expired(self) -> bool:
        expires_at = self.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) > expires_at

    def revoke(self) -> None:
        self.revoked = True