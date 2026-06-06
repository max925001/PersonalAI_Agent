from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class UserSignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserProfileResponse(BaseModel):
    id: str
    email: EmailStr
    is_active: bool

class TokenVerificationResponse(BaseModel):
    authenticated: bool
    reason: Optional[str] = None