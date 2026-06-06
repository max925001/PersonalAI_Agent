from fastapi import APIRouter, Depends, Response, Request, status
from jose import ExpiredSignatureError, JWTError
from app.core.exceptions import UnauthorizedException
from app.application.auth.use_cases import SignupUseCase, LoginUseCase, RefreshSessionUseCase, LogoutUseCase
from app.application.auth.dtos import SignupInput, LoginInput
from app.domain.auth.entities import User
from app.application.auth.security_service import ISecurityService
from app.infrastructure.web.schemas.auth_schemas import UserSignupRequest, UserLoginRequest, UserProfileResponse, TokenVerificationResponse
from app.infrastructure.web.dependencies import (
    get_signup_uc,
    get_login_uc,
    get_refresh_uc,
    get_logout_uc,
    get_current_user,
    get_security_service
)

from app.core.config import settings

router = APIRouter()

# Cookie Parameters - Dynamic based on environment
if settings.APP_ENV == "production":
    COOKIE_PARAMS = {
        "httponly": True,
        "secure": True,
        "samesite": "none",
    }
else:
    COOKIE_PARAMS = {
        "httponly": True,
        "secure": False,
        "samesite": "lax",
    }


@router.post("/signup", status_code=status.HTTP_201_CREATED, response_model=UserProfileResponse)
async def signup(
    payload: UserSignupRequest, 
    use_case: SignupUseCase = Depends(get_signup_uc)
) -> UserProfileResponse:
    """Registers a new user profile."""
    dto = SignupInput(email=payload.email, password=payload.password)
    user = await use_case.execute(dto)
    return UserProfileResponse(
        id=str(user.id),
        email=user.email.value,
        is_active=user.is_active
    )


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(
    response: Response, 
    payload: UserLoginRequest, 
    use_case: LoginUseCase = Depends(get_login_uc)
):
    """Authenticates credentials and sets secure HttpOnly cookies."""
    dto = LoginInput(email=payload.email, password=payload.password)
    tokens = await use_case.execute(dto)
    
    # Store BOTH tokens in HttpOnly secure cookies
    response.set_cookie(key="access_token", value=tokens.access_token, max_age=900, **COOKIE_PARAMS)
    response.set_cookie(key="refresh_token", value=tokens.refresh_token, max_age=604800, **COOKIE_PARAMS)
    
    return {"message": "Success"}


@router.get("/me", response_model=UserProfileResponse, status_code=status.HTTP_200_OK)
async def get_me(current_user: User = Depends(get_current_user)) -> UserProfileResponse:
    """Returns the authenticated user profile."""
    return UserProfileResponse(
        id=str(current_user.id),
        email=current_user.email.value,
        is_active=current_user.is_active
    )


@router.post("/refresh", status_code=status.HTTP_200_OK)
async def refresh_session(
    request: Request,
    response: Response,
    use_case: RefreshSessionUseCase = Depends(get_refresh_uc)
):
    """Refreshes the session using the refresh token from cookies (RTR enabled)."""
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise UnauthorizedException("Refresh token is missing from cookies")

    tokens = await use_case.execute(refresh_token)
    
    # Overwrite cookies with rotated tokens
    response.set_cookie(key="access_token", value=tokens.access_token, max_age=900, **COOKIE_PARAMS)
    response.set_cookie(key="refresh_token", value=tokens.refresh_token, max_age=604800, **COOKIE_PARAMS)
    
    return {"message": "Session refreshed"}


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    request: Request,
    response: Response,
    use_case: LogoutUseCase = Depends(get_logout_uc)
):
    """Revokes the refresh token and clears all cookies."""
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        await use_case.execute(refresh_token)
        
    # Clear cookies by setting expired Max-Age
    response.set_cookie(key="access_token", value="", max_age=0, **COOKIE_PARAMS)
    response.set_cookie(key="refresh_token", value="", max_age=0, **COOKIE_PARAMS)
    
    return {"message": "Logged out successfully"}


@router.get("/verify", response_model=TokenVerificationResponse, status_code=status.HTTP_200_OK)
async def verify_token(
    request: Request,
    security: ISecurityService = Depends(get_security_service)
) -> TokenVerificationResponse:
    """Checks the validity of the access token cookie."""
    token = request.cookies.get("access_token")
    if not token:
        return TokenVerificationResponse(authenticated=False, reason="missing_token")
        
    try:
        security.decode_jwt(token)
        return TokenVerificationResponse(authenticated=True)
    except ExpiredSignatureError:
        return TokenVerificationResponse(authenticated=False, reason="token_expired")
    except JWTError:
        return TokenVerificationResponse(authenticated=False, reason="invalid_token")
    except Exception:
        return TokenVerificationResponse(authenticated=False, reason="invalid_token")