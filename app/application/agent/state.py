from typing import TypedDict, List, Dict, Any, Optional

class AgentState(TypedDict):
    session_id: str
    message: str
    chat_history: List[Dict[str, Any]]
    retrieved_context: List[Dict[str, Any]]
    response: Optional[str]
    confidence_score: str  # "high", "medium", "low"
    sources: List[Dict[str, Any]]
    intent: Optional[str]  # "rag", "greeting", "schedule_list", "schedule_book"
    voice_mode: Optional[bool]
