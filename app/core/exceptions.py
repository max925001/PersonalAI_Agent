from fastapi import HTTPException, status

class AppException(Exception):
    """Base application exception for custom error boundaries."""
    def __init__(self, message: str, code: str = "INTERNAL_SERVER_ERROR", status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


class EntityNotFoundException(AppException):
    """Exception raised when a requested resource/entity does not exist."""
    def __init__(self, message: str = "Resource not found", code: str = "NOT_FOUND"):
        super().__init__(message, code, status_code=status.HTTP_404_NOT_FOUND)


class UnauthorizedException(AppException):
    """Exception raised when authorization checks fail."""
    def __init__(self, message: str = "Unauthorized access", code: str = "UNAUTHORIZED"):
        super().__init__(message, code, status_code=status.HTTP_401_UNAUTHORIZED)


class ForbiddenException(AppException):
    """Exception raised when access to a resource is forbidden."""
    def __init__(self, message: str = "Access forbidden", code: str = "FORBIDDEN"):
        super().__init__(message, code, status_code=status.HTTP_403_FORBIDDEN)


class ConflictException(AppException):
    """Exception raised when resource state conflicts occur."""
    def __init__(self, message: str = "Resource conflict occurred", code: str = "CONFLICT"):
        super().__init__(message, code, status_code=status.HTTP_409_CONFLICT)


class ValidationException(AppException):
    """Exception raised for business logic validation failures."""
    def __init__(self, message: str = "Validation failed", code: str = "VALIDATION_FAILED"):
        super().__init__(message, code, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


class CloudinaryException(AppException):
    """Exception raised when Cloudinary storage operations fail."""
    def __init__(self, message: str = "Cloudinary storage error", code: str = "CLOUDINARY_ERROR"):
        super().__init__(message, code, status_code=status.HTTP_502_BAD_GATEWAY)


class GitHubException(AppException):
    """Exception raised when GitHub API ingestion fails."""
    def __init__(self, message: str = "GitHub API error", code: str = "GITHUB_ERROR"):
        super().__init__(message, code, status_code=status.HTTP_502_BAD_GATEWAY)


class ResumeProcessingException(AppException):
    """Exception raised during PDF text extraction and parsing."""
    def __init__(self, message: str = "Resume processing error", code: str = "RESUME_PROCESSING_ERROR"):
        super().__init__(message, code, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


class EmbeddingException(AppException):
    """Exception raised when Gemini embedding generation fails."""
    def __init__(self, message: str = "Embedding generation error", code: str = "EMBEDDING_ERROR"):
        super().__init__(message, code, status_code=status.HTTP_502_BAD_GATEWAY)


class QdrantException(AppException):
    """Exception raised when Qdrant vector store operations fail."""
    def __init__(self, message: str = "Qdrant vector store error", code: str = "QDRANT_ERROR"):
        super().__init__(message, code, status_code=status.HTTP_502_BAD_GATEWAY)


class DatabaseException(AppException):
    """Exception raised when MongoDB database operations fail."""
    def __init__(self, message: str = "Database operation error", code: str = "DATABASE_ERROR"):
        super().__init__(message, code, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChatException(AppException):
    """Exception raised when chat RAG operations fail."""
    def __init__(self, message: str = "Chat processing error", code: str = "CHAT_ERROR"):
        super().__init__(message, code, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
