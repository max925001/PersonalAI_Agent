from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    APP_NAME: str = "AI Shivam"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    API_V1_PREFIX: str = "/api/v1"
    JWT_SECRET_KEY: str = "ai_shivam_development_secret_key_change_me_in_production"
    
    # MongoDB Atlas Connection Parameters
    MONGO_URI: str = "mongodb+srv://user:pass@cluster.mongodb.net/ai_twin_db?retryWrites=true&w=majority"
    MONGO_DB_NAME: str = "ai_twin_db"
    
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Qdrant Vector DB Settings
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_URL: Optional[str] = None
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION_NAME: str = "shivam_knowledge_base"
    QDRANT_TIMEOUT: float = 60.0
    
    # AI Credentials
    GEMINI_API_KEY: str = "gemini-key"
    GOOGLE_API_KEY: Optional[str] = None
    GROQ_API_KEY: str = "groq-key"
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    ELEVENLABS_API_KEY: str = "eleven-key"
    ELEVENLABS_VOICE_ID: str = "IKne3meq5aSn9XLyUdCD"
    ELEVENLABS_STABILITY: float = 0.4
    ELEVENLABS_SIMILARITY_BOOST: float = 0.85
    
    # Cloudinary Storage
    CLOUDINARY_CLOUD_NAME: str = "cloud-name"
    CLOUDINARY_API_KEY: str = "cloudinary-key"
    CLOUDINARY_API_SECRET: str = "cloudinary-secret"
    
    # GitHub Integration
    GITHUB_TOKEN: str = ""
    
    # S3 Storage (Legacy/Fallback)
    S3_BUCKET_NAME: str = "bucket"
    AWS_ACCESS_KEY_ID: str = "aws-id"
    AWS_SECRET_ACCESS_KEY: str = "aws-key"
    AWS_REGION_NAME: str = "us-east-1"
    
    LOG_LEVEL: str = "INFO"
    
    # Twilio Integration Settings
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_VOICE_LIMIT_SECONDS: int = 600
    PUBLIC_URL: Optional[str] = None
    FRONTEND_URL: Optional[str] = None

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()