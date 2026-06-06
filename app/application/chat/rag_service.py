from typing import List, Dict, Any, Tuple
from loguru import logger

class RAGService:
    """Service that formats retrieved vectors into context and prompt constructs, and scores responses."""

    def __init__(self):
        self.token_budget = 4000  # Character-based approximation of token budget for context

    def build_context(self, chunks: List[Dict[str, Any]]) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Formats retrieved vector hits into context and extracts source citations.
        Applies character token budget management (clipping).
        """
        context_parts = []
        sources = []
        char_count = 0
        
        for idx, hit in enumerate(chunks):
            payload = hit.get("payload", {})
            text = payload.get("chunk_text") or ""
            
            # Context compression / Token Budget check
            if char_count + len(text) > self.token_budget:
                logger.warning(f"Retrieved context exceeds character budget. Clipping at index {idx}.")
                break
                
            char_count += len(text)
            
            # Format block
            source_type = payload.get("source_type", "unknown")
            source_id = payload.get("source_id", "unknown")
            repo_name = payload.get("repository_name", "")
            
            context_parts.append(
                f"[{idx + 1}] Source Type: {source_type}\n"
                f"Source ID: {source_id}\n"
                f"Repository: {repo_name if repo_name else 'N/A'}\n"
                f"Content:\n{text}\n"
                f"----------------------------------------"
            )
            
            # Extract source citation
            sources.append({
                "source_type": source_type,
                "source_id": source_id,
                "repository_name": repo_name
            })
            
        return "\n".join(context_parts), sources

    def calculate_confidence(self, chunks: List[Dict[str, Any]]) -> str:
        """
        Determines the RAG confidence level based on chunk count and search scores.
        Returns: "high", "medium", or "low".
        """
        if not chunks:
            return "low"
            
        avg_score = sum(hit.get("score", 0) for hit in chunks) / len(chunks)
        
        # Scoring business rule
        if avg_score >= 0.75 and len(chunks) >= 3:
            return "high"
        elif avg_score >= 0.60:
            return "medium"
        else:
            return "low"
