import uuid
from datetime import datetime, timedelta, timezone
from app.core.exceptions import ConflictException, UnauthorizedException
from app.domain.auth.entities import User, RefreshTokenSession
from app.domain.auth.value_objects import Email, PasswordHash
from app.domain.auth.repository_interfaces import IUserRepository, IRefreshTokenRepository
from app.application.auth.security_service import ISecurityService
from app.application.auth.dtos import SignupInput, LoginInput, AuthTokenResult


class SignupUseCase:
    """Handles new user signup with email syntax and duplicate checking."""
    def __init__(self, user_repo: IUserRepository, security: ISecurityService):
        self.user_repo = user_repo
        self.security = security

    async def execute(self, data: SignupInput) -> User:
        email_vo = Email(data.email)
        
        # Check duplicate registration
        existing = await self.user_repo.get_by_email(email_vo)
        if existing:
            raise ConflictException("Email already registered")
            
        hashed_pwd = self.security.hash_password(data.password)
        new_user = User(email=email_vo, password_hash=PasswordHash(hashed_pwd))
        return await self.user_repo.save(new_user)


class LoginUseCase:
    """Authenticates credentials, generates JWT pair, and stores refresh token hash."""
    def __init__(
        self, 
        user_repo: IUserRepository, 
        token_repo: IRefreshTokenRepository, 
        security: ISecurityService
    ):
        self.user_repo = user_repo
        self.token_repo = token_repo
        self.security = security

    async def execute(self, data: LoginInput) -> AuthTokenResult:
        user = await self.user_repo.get_by_email(Email(data.email))
        if not user or not self.security.verify_password(data.password, user.password_hash.value):
            raise UnauthorizedException("Invalid email or password")
            
        # Generate Access Token (15 mins)
        access_token = self.security.generate_jwt(
            subject=str(user.id), 
            expires_delta=timedelta(minutes=15), 
            token_type="access"
        )
        
        # Generate Refresh Token (7 days)
        refresh_token = self.security.generate_jwt(
            subject=str(user.id), 
            expires_delta=timedelta(days=7), 
            token_type="refresh"
        )
        
        # Save token session hash in PostgreSQL
        token_hash = self.security.hash_token(refresh_token)
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        
        session = RefreshTokenSession(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at
        )
        await self.token_repo.save(session)
        
        return AuthTokenResult(access_token=access_token, refresh_token=refresh_token)


class RefreshSessionUseCase:
    """
    Validates the refresh token, performs rotation, and implements replay attack detection.
    """
    def __init__(
        self, 
        user_repo: IUserRepository, 
        token_repo: IRefreshTokenRepository, 
        security: ISecurityService
    ):
        self.user_repo = user_repo
        self.token_repo = token_repo
        self.security = security

    async def execute(self, refresh_token: str) -> AuthTokenResult:
        try:
            payload = self.security.decode_jwt(refresh_token)
            if payload.get("typ") != "refresh":
                raise UnauthorizedException("Invalid token type")
            user_id_str = payload.get("sub")
            user_id = uuid.UUID(user_id_str)
        except Exception as e:
            raise UnauthorizedException("Malformed or expired refresh token") from e

        token_hash = self.security.hash_token(refresh_token)
        session = await self.token_repo.get_by_hash(token_hash)
        
        if not session:
            raise UnauthorizedException("Refresh session not found")

        # Replay Attack Detection
        if session.revoked:
            # Stolen refresh token reused. Invalidate all user sessions immediately.
            await self.token_repo.revoke_all_by_user(user_id)
            raise UnauthorizedException("Replay attack detected. Session terminated.")

        if session.is_expired:
            raise UnauthorizedException("Refresh token has expired")

        # Invalidate old session token
        session.revoke()
        await self.token_repo.save(session)

        # Generate new tokens (Rotation)
        new_access = self.security.generate_jwt(str(user_id), timedelta(minutes=15), "access")
        new_refresh = self.security.generate_jwt(str(user_id), timedelta(days=7), "refresh")

        new_hash = self.security.hash_token(new_refresh)
        new_expires = datetime.now(timezone.utc) + timedelta(days=7)

        new_session = RefreshTokenSession(
            user_id=user_id,
            token_hash=new_hash,
            expires_at=new_expires
        )
        await self.token_repo.save(new_session)

        return AuthTokenResult(access_token=new_access, refresh_token=new_refresh)


class LogoutUseCase:
    """Revokes the current refresh token and logs out the user."""
    def __init__(self, token_repo: IRefreshTokenRepository, security: ISecurityService):
        self.token_repo = token_repo
        self.security = security

    async def execute(self, refresh_token: str) -> None:
        try:
            token_hash = self.security.hash_token(refresh_token)
            session = await self.token_repo.get_by_hash(token_hash)
            if session:
                session.revoke()
                await self.token_repo.save(session)
        except Exception:
            pass  # Fail silently on logout token decode issues