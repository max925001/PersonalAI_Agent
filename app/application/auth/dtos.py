from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class SignupInput:
    email: str
    password: str


@dataclass(frozen=True)
class LoginInput:
    email: str
    password: str


@dataclass(frozen=True)
class AuthTokenResult:
    access_token: str
    refresh_token: str