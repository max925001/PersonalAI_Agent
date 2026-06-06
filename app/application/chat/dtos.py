from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ChatRequest(BaseModel):
    message: str = Field(..., description="Message from the recruiter")
    session_id: Optional[str] = Field(None, description="UUID session identifier for chat history lookup")

class Citation(BaseModel):
    source_type: str = Field(..., description="E.g. resume or repository")
    source_id: str = Field(..., description="Reference document ID")
    repository_name: Optional[str] = Field(None, description="Optional GitHub repository name")

class ChatResponse(BaseModel):
    answer: str = Field(..., description="Generative response from AI Representative")
    sources: List[Citation] = Field(..., description="List of source citations grounded in vector store")
    confidence: str = Field(..., description="Confidence score representing match quality: high, medium, low")
    elapsed_time_seconds: float = Field(..., description="Response latency in seconds")
