from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.core.config import settings
from app.infrastructure.persistence.mongodb.documents.user_document import UserDocument
from app.infrastructure.persistence.mongodb.documents.token_document import RefreshTokenDocument
from app.infrastructure.persistence.mongodb.documents.profile_document import ProfileDocument
from app.infrastructure.persistence.mongodb.documents.resume_document import ResumeDocument
from app.infrastructure.persistence.mongodb.documents.github_repo_document import GitHubRepositoryDocument
from app.infrastructure.persistence.mongodb.documents.availability_document import AvailabilityDocument
from app.infrastructure.persistence.mongodb.documents.knowledge_document import KnowledgeDocumentDocument
from app.infrastructure.persistence.mongodb.documents.processing_status_document import ProcessingStatusDocument
from app.infrastructure.persistence.mongodb.documents.embedding_job_document import EmbeddingJobDocument
from app.infrastructure.persistence.mongodb.documents.conversation_document import ConversationDocument
from app.infrastructure.persistence.mongodb.documents.message_document import MessageDocument
from app.infrastructure.persistence.mongodb.documents.call_session_document import CallSessionDocument
from loguru import logger

# Monkey-patch AsyncIOMotorClient to support append_metadata
# This prevents Beanie ODM from crashing on startup under modern Motor/PyMongo versions
if not hasattr(AsyncIOMotorClient, "append_metadata"):
    def dummy_append_metadata(*args, **kwargs):
        pass
    AsyncIOMotorClient.append_metadata = dummy_append_metadata

_mongo_client: AsyncIOMotorClient = None

async def init_database() -> None:
    global _mongo_client
    logger.info("Initializing MongoDB Atlas connection via Beanie ODM...")
    
    _mongo_client = AsyncIOMotorClient(settings.MONGO_URI)
    database = _mongo_client[settings.MONGO_DB_NAME]
    
    await init_beanie(
        database=database,
        document_models=[
            UserDocument,
            RefreshTokenDocument,
            ProfileDocument,
            ResumeDocument,
            GitHubRepositoryDocument,
            AvailabilityDocument,
            KnowledgeDocumentDocument,
            ProcessingStatusDocument,
            EmbeddingJobDocument,
            ConversationDocument,
            MessageDocument,
            CallSessionDocument
        ]
    )
    logger.info("Database and ODM initialization completed.")

def close_connections() -> None:
    global _mongo_client
    if _mongo_client:
        _mongo_client.close()
        logger.info("MongoDB connection pool closed.")