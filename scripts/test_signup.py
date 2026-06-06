import asyncio
import sys
from app.core.config import settings
from app.infrastructure.persistence.mongodb.database import init_database, close_connections
from app.application.auth.use_cases import SignupUseCase
from app.application.auth.dtos import SignupInput
from app.infrastructure.persistence.mongodb.repositories.user_repository import BeanieUserRepository
from app.infrastructure.adapters.security.jwt_security_adapter import JwtSecurityAdapter
from app.core.exceptions import ConflictException

async def main():
    print("Initializing MongoDB Atlas connection...")
    await init_database()
    
    user_repo = BeanieUserRepository()
    security = JwtSecurityAdapter(secret_key=settings.JWT_SECRET_KEY, algorithm="HS256")
    signup_uc = SignupUseCase(user_repo, security)
    
    # Try signing up a test user
    email = "shivam_test@example.com"
    password = "password123"
    
    print(f"Attempting to register email: {email}...")
    dto = SignupInput(email=email, password=password)
    
    try:
        user = await signup_uc.execute(dto)
        print(f"Signup successful! User ID: {user.id}, Email: {user.email.value}")
    except ConflictException as e:
        print(f"Successfully caught ConflictException: {e.message} (code: {e.code})")
    except ValueError as e:
        print(f"Successfully caught ValueError: {str(e)}")
    except Exception as e:
        print(f"Unexpected error during signup: {e}")
        import traceback
        traceback.print_exc()

    # Try signing up the same user to verify conflict error handling
    print("\nAttempting to register the same email again to test duplicate check...")
    try:
        await signup_uc.execute(dto)
        print("Error: Expected ConflictException but signup succeeded!")
    except ConflictException as e:
        print(f"Success! Correctly caught duplicate registration error: status={e.status_code}, code={e.code}, msg={e.message}")
    except Exception as e:
        print(f"Unexpected error during duplicate signup check: {e}")

    close_connections()

if __name__ == "__main__":
    asyncio.run(main())
