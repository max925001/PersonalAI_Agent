from __future__ import annotations
from fastapi import Depends, Request
import uuid

from app.core.config import settings
from app.core.exceptions import UnauthorizedException
from app.domain.auth.entities import User
from app.domain.auth.repository_interfaces import IUserRepository, IRefreshTokenRepository
from app.domain.profile.repository_interfaces import (
    IProfileRepository, IResumeRepository, IGitHubRepositoryRepository,
    IAvailabilityRepository, IKnowledgeDocumentRepository, IProcessingStatusRepository,
    IEmbeddingJobRepository
)
from app.application.interfaces.storage_port import IStoragePort
from app.application.interfaces.github_port import IGitHubPort
from app.application.interfaces.embedding_port import IEmbeddingPort
from app.application.interfaces.vector_db_port import IVectorDatabasePort

from app.application.auth.security_service import ISecurityService
from app.application.auth.use_cases import SignupUseCase, LoginUseCase, RefreshSessionUseCase, LogoutUseCase
from app.infrastructure.adapters.security.jwt_security_adapter import JwtSecurityAdapter
from app.infrastructure.persistence.mongodb.repositories.user_repository import BeanieUserRepository
from app.infrastructure.persistence.mongodb.repositories.token_repository import BeanieRefreshTokenRepository

from app.application.profile.resume_processor import ResumeProcessor
from app.application.profile.github_service import GitHubService
from app.application.profile.repository_sync_service import RepositorySyncService
from app.application.profile.knowledge_document_service import KnowledgeDocumentService
from app.application.profile.chunking_service import ChunkingService
from app.application.profile.embedding_service import EmbeddingService
from app.application.profile.qdrant_service import QdrantService
from app.application.profile.scheduling_service import SchedulingService
from app.application.profile.background_orchestrator import BackgroundJobOrchestrator

def get_security_service() -> ISecurityService:
    return JwtSecurityAdapter(
        secret_key=settings.JWT_SECRET_KEY,
        algorithm="HS256"
    )

def get_user_repository() -> IUserRepository:
    return BeanieUserRepository()

def get_token_repository() -> IRefreshTokenRepository:
    return BeanieRefreshTokenRepository()

def get_signup_uc(
    user_repo: IUserRepository = Depends(get_user_repository),
    security: ISecurityService = Depends(get_security_service)
) -> SignupUseCase:
    return SignupUseCase(user_repo, security)

def get_login_uc(
    user_repo: IUserRepository = Depends(get_user_repository),
    token_repo: IRefreshTokenRepository = Depends(get_token_repository),
    security: ISecurityService = Depends(get_security_service)
) -> LoginUseCase:
    return LoginUseCase(user_repo, token_repo, security)

def get_refresh_uc(
    user_repo: IUserRepository = Depends(get_user_repository),
    token_repo: IRefreshTokenRepository = Depends(get_token_repository),
    security: ISecurityService = Depends(get_security_service)
) -> RefreshSessionUseCase:
    return RefreshSessionUseCase(user_repo, token_repo, security)

def get_logout_uc(
    token_repo: IRefreshTokenRepository = Depends(get_token_repository),
    security: ISecurityService = Depends(get_security_service)
) -> LogoutUseCase:
    return LogoutUseCase(token_repo, security)

async def get_current_user(
    request: Request,
    user_repo: IUserRepository = Depends(get_user_repository),
    security: ISecurityService = Depends(get_security_service)
) -> User:
    token = request.cookies.get("access_token")
    if not token:
        raise UnauthorizedException("Access token is missing from cookies")

    try:
        payload = security.decode_jwt(token)
        if payload.get("typ") != "access":
            raise UnauthorizedException("Invalid token type presented")
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise UnauthorizedException("User subject is missing in token payload")
    except Exception as e:
        raise UnauthorizedException("Invalid or expired access token") from e

    user = await user_repo.get_by_id(uuid.UUID(user_id_str))
    if not user or not user.is_active:
        raise UnauthorizedException("User profile is inactive or does not exist")
        
    return user


# Repositories
def get_profile_repository() -> IProfileRepository:
    from app.infrastructure.persistence.mongodb.repositories.profile_repository import BeanieProfileRepository
    return BeanieProfileRepository()

def get_resume_repository() -> IResumeRepository:
    from app.infrastructure.persistence.mongodb.repositories.resume_repository import BeanieResumeRepository
    return BeanieResumeRepository()

def get_github_repo_repository() -> IGitHubRepositoryRepository:
    from app.infrastructure.persistence.mongodb.repositories.github_repo_repository import BeanieGitHubRepositoryRepository
    return BeanieGitHubRepositoryRepository()

def get_availability_repository() -> IAvailabilityRepository:
    from app.infrastructure.persistence.mongodb.repositories.availability_repository import BeanieAvailabilityRepository
    return BeanieAvailabilityRepository()

def get_knowledge_document_repository() -> IKnowledgeDocumentRepository:
    from app.infrastructure.persistence.mongodb.repositories.knowledge_document_repository import BeanieKnowledgeDocumentRepository
    return BeanieKnowledgeDocumentRepository()

def get_processing_status_repository() -> IProcessingStatusRepository:
    from app.infrastructure.persistence.mongodb.repositories.processing_status_repository import BeanieProcessingStatusRepository
    return BeanieProcessingStatusRepository()

def get_embedding_job_repository() -> IEmbeddingJobRepository:
    from app.infrastructure.persistence.mongodb.repositories.embedding_job_repository import BeanieEmbeddingJobRepository
    return BeanieEmbeddingJobRepository()


# Storage & Third-Party Adapters
def get_storage_port() -> IStoragePort:
    from app.infrastructure.adapters.storage.cloudinary_adapter import CloudinaryStorageAdapter
    return CloudinaryStorageAdapter()

def get_github_port() -> IGitHubPort:
    from app.infrastructure.adapters.github.github_client_adapter import GitHubClientAdapter
    return GitHubClientAdapter()

_embedding_adapter_instance = None

def get_embedding_port() -> IEmbeddingPort:
    global _embedding_adapter_instance
    if _embedding_adapter_instance is None:
        from app.infrastructure.adapters.ai.sentence_transformers_adapter import SentenceTransformersEmbeddingAdapter
        _embedding_adapter_instance = SentenceTransformersEmbeddingAdapter()
    return _embedding_adapter_instance

_vector_db_adapter_instance = None

def get_vector_db_port() -> IVectorDatabasePort:
    global _vector_db_adapter_instance
    if _vector_db_adapter_instance is None:
        from app.infrastructure.persistence.qdrant.qdrant_adapter import QdrantAdapter
        _vector_db_adapter_instance = QdrantAdapter()
    return _vector_db_adapter_instance


# Services
def get_resume_processor(
    resume_repo: IResumeRepository = Depends(get_resume_repository)
) -> ResumeProcessor:
    from app.application.profile.resume_processor import ResumeProcessor
    return ResumeProcessor(resume_repo)

def get_github_service(
    github_port: IGitHubPort = Depends(get_github_port)
) -> GitHubService:
    from app.application.profile.github_service import GitHubService
    return GitHubService(github_port)

def get_sync_service(
    repo_repository: IGitHubRepositoryRepository = Depends(get_github_repo_repository)
) -> RepositorySyncService:
    from app.application.profile.repository_sync_service import RepositorySyncService
    return RepositorySyncService(repo_repository)

def get_knowledge_document_service(
    knowledge_repo: IKnowledgeDocumentRepository = Depends(get_knowledge_document_repository)
) -> KnowledgeDocumentService:
    from app.application.profile.knowledge_document_service import KnowledgeDocumentService
    return KnowledgeDocumentService(knowledge_repo)

def get_chunking_service() -> ChunkingService:
    from app.application.profile.chunking_service import ChunkingService
    return ChunkingService()

def get_embedding_service(
    embedding_port: IEmbeddingPort = Depends(get_embedding_port)
) -> EmbeddingService:
    from app.application.profile.embedding_service import EmbeddingService
    return EmbeddingService(embedding_port)

def get_qdrant_service(
    vector_db_port: IVectorDatabasePort = Depends(get_vector_db_port)
) -> QdrantService:
    from app.application.profile.qdrant_service import QdrantService
    return QdrantService(vector_db_port)

def get_scheduling_service(
    availability_repo = Depends(get_availability_repository)
) -> SchedulingService:
    from fastapi.params import Depends
    if isinstance(availability_repo, Depends):
        availability_repo = get_availability_repository()
        
    from app.application.profile.scheduling_service import SchedulingService
    return SchedulingService(availability_repo)

def get_background_orchestrator(
    profile_repo: IProfileRepository = Depends(get_profile_repository),
    resume_repo: IResumeRepository = Depends(get_resume_repository),
    status_repo: IProcessingStatusRepository = Depends(get_processing_status_repository),
    embedding_job_repo: IEmbeddingJobRepository = Depends(get_embedding_job_repository),
    resume_processor: ResumeProcessor = Depends(get_resume_processor),
    github_service: GitHubService = Depends(get_github_service),
    sync_service: RepositorySyncService = Depends(get_sync_service),
    knowledge_service: KnowledgeDocumentService = Depends(get_knowledge_document_service),
    chunking_service: ChunkingService = Depends(get_chunking_service),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    qdrant_service: QdrantService = Depends(get_qdrant_service),
    embedding_port: IEmbeddingPort = Depends(get_embedding_port)
) -> BackgroundJobOrchestrator:
    from app.application.profile.background_orchestrator import BackgroundJobOrchestrator
    return BackgroundJobOrchestrator(
        profile_repo=profile_repo,
        resume_repo=resume_repo,
        status_repo=status_repo,
        embedding_job_repo=embedding_job_repo,
        resume_processor=resume_processor,
        github_service=github_service,
        sync_service=sync_service,
        knowledge_service=knowledge_service,
        chunking_service=chunking_service,
        embedding_service=embedding_service,
        qdrant_service=qdrant_service,
        embedding_port=embedding_port
    )

# Chat & RAG Dependencies
def get_conversation_repository():
    from app.infrastructure.persistence.mongodb.repositories.conversation_repository import BeanieConversationRepository
    return BeanieConversationRepository()

def get_message_repository():
    from app.infrastructure.persistence.mongodb.repositories.message_repository import BeanieMessageRepository
    return BeanieMessageRepository()

_llm_adapter_instance = None

def get_llm_port():
    global _llm_adapter_instance
    if _llm_adapter_instance is None:
        from app.infrastructure.adapters.ai.groq_llm_adapter import GroqLlmAdapter
        _llm_adapter_instance = GroqLlmAdapter()
    return _llm_adapter_instance

def get_retriever_service(
    embedding_port = Depends(get_embedding_port),
    vector_db_port = Depends(get_vector_db_port)
):
    from fastapi.params import Depends
    if isinstance(embedding_port, Depends):
        embedding_port = get_embedding_port()
    if isinstance(vector_db_port, Depends):
        vector_db_port = get_vector_db_port()
        
    from app.application.chat.retriever_service import RetrieverService
    return RetrieverService(embedding_port, vector_db_port)

def get_memory_service(
    conversation_repo = Depends(get_conversation_repository),
    message_repo = Depends(get_message_repository)
):
    from fastapi.params import Depends
    if isinstance(conversation_repo, Depends):
        conversation_repo = get_conversation_repository()
    if isinstance(message_repo, Depends):
        message_repo = get_message_repository()
        
    from app.application.chat.memory_service import MemoryService
    return MemoryService(conversation_repo, message_repo)

def get_rag_service():
    from app.application.chat.rag_service import RAGService
    return RAGService()

def get_agent_nodes(
    retriever_service = Depends(get_retriever_service),
    memory_service = Depends(get_memory_service),
    rag_service = Depends(get_rag_service),
    llm_port = Depends(get_llm_port),
    scheduling_service = Depends(get_scheduling_service),
    profile_repo = Depends(get_profile_repository)
):
    from fastapi.params import Depends
    if isinstance(retriever_service, Depends):
        retriever_service = get_retriever_service()
    if isinstance(memory_service, Depends):
        memory_service = get_memory_service()
    if isinstance(rag_service, Depends):
        rag_service = get_rag_service()
    if isinstance(llm_port, Depends):
        llm_port = get_llm_port()
    if isinstance(scheduling_service, Depends):
        scheduling_service = get_scheduling_service()
    if isinstance(profile_repo, Depends):
        profile_repo = get_profile_repository()
        
    from app.application.agent.nodes import AgentNodes
    return AgentNodes(
        retriever_service=retriever_service,
        memory_service=memory_service,
        rag_service=rag_service,
        llm_port=llm_port,
        scheduling_service=scheduling_service,
        profile_repo=profile_repo
    )

_agent_use_case_instance = None

def get_agent_use_case(
    nodes = Depends(get_agent_nodes)
):
    from fastapi.params import Depends
    if isinstance(nodes, Depends):
        nodes = get_agent_nodes()
        
    global _agent_use_case_instance
    if _agent_use_case_instance is None:
        from app.application.agent.agent_use_case import AgentUseCase
        _agent_use_case_instance = AgentUseCase(nodes)
    return _agent_use_case_instance

_call_session_service_instance = None

def get_call_session_service():
    global _call_session_service_instance
    if _call_session_service_instance is None:
        from app.application.voice.call_session_service import CallSessionService
        _call_session_service_instance = CallSessionService()
    return _call_session_service_instance

_twilio_voice_pipeline_instance = None

def get_twilio_voice_pipeline(
    agent_use_case = Depends(get_agent_use_case)
):
    from fastapi.params import Depends
    if isinstance(agent_use_case, Depends):
        agent_use_case = get_agent_use_case()
        
    global _twilio_voice_pipeline_instance
    if _twilio_voice_pipeline_instance is None:
        from app.application.voice.twilio_voice_pipeline import TwilioVoicePipeline
        _twilio_voice_pipeline_instance = TwilioVoicePipeline(agent_use_case)
    return _twilio_voice_pipeline_instance