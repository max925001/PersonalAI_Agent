import time
from typing import Dict, Any
from loguru import logger

from app.application.agent.graph import create_agent_graph
from app.application.agent.nodes import AgentNodes

class AgentUseCase:
    """Orchestrator class executing the LangGraph chat RAG pipeline and calculating observability metrics."""

    def __init__(self, agent_nodes: AgentNodes):
        self.graph = create_agent_graph(agent_nodes)
        logger.info("AgentUseCase compiled StateGraph successfully.")

    async def execute(self, session_id: str, message: str, voice_mode: bool = False) -> Dict[str, Any]:
        import uuid
        
        # Resolve/normalize session_id
        session_id_str = session_id
        if not session_id_str:
            session_id_str = str(uuid.uuid4())
        else:
            try:
                uuid.UUID(session_id_str)
            except ValueError:
                deterministic_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, session_id_str)
                session_id_str = str(deterministic_uuid)
                
        logger.info(f"AgentUseCase executing request for session {session_id} (resolved to {session_id_str})...")
        start_time = time.time()
        
        # Initial State
        initial_state = {
            "session_id": session_id_str,
            "message": message,
            "chat_history": [],
            "retrieved_context": [],
            "response": None,
            "confidence_score": "low",
            "sources": [],
            "intent": None,
            "voice_mode": voice_mode
        }
        
        # Execute the Compiled Graph
        try:
            final_state = await self.graph.ainvoke(initial_state)
            elapsed_time = time.time() - start_time
            logger.info(f"AgentUseCase complete. Total elapsed time: {elapsed_time:.4f}s")
            
            return {
                "response": final_state.get("response") or "I don't have enough information to answer that.",
                "sources": final_state.get("sources") or [],
                "confidence_score": final_state.get("confidence_score") or "low",
                "elapsed_time_seconds": elapsed_time
            }
        except Exception as e:
            logger.exception("LangGraph execution crashed. Returning fallback response.")
            elapsed_time = time.time() - start_time
            return {
                "response": "I don't have enough information to answer that.",
                "sources": [],
                "confidence_score": "low",
                "elapsed_time_seconds": elapsed_time
            }
