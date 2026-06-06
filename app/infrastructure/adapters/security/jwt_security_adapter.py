import hashlib
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
from jose import jwt
import bcrypt
from app.application.auth.security_service import ISecurityService

class JwtSecurityAdapter(ISecurityService):
    def __init__(self, secret_key: str, algorithm: str):
        self.secret_key = secret_key
        self.algorithm = algorithm

    def hash_password(self, password: str) -> str:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"),
                hashed_password.encode("utf-8")
            )
        except Exception:
            return False

    def generate_jwt(self, subject: str, expires_delta: timedelta, token_type: str) -> str:
        expire = datetime.now(timezone.utc) + expires_delta
        payload = {"sub": subject, "exp": expire, "typ": token_type}
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def decode_jwt(self, token: str) -> Dict[str, Any]:
        return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

    def hash_token(self, token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()