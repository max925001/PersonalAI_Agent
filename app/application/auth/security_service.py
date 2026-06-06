from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Dict, Any

class ISecurityService(ABC):
    @abstractmethod
    def hash_password(self, password: str) -> str:
        pass

    @abstractmethod
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        pass

    @abstractmethod
    def generate_jwt(self, subject: str, expires_delta: timedelta, token_type: str) -> str:
        pass

    @abstractmethod
    def decode_jwt(self, token: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def hash_token(self, token: str) -> str:
        pass