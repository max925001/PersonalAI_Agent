from abc import ABC, abstractmethod
from typing import Optional

class ILLMPort(ABC):
    """Port contract for generating text responses from an LLM."""

    @abstractmethod
    async def generate_response(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.0,
        max_output_tokens: Optional[int] = None
    ) -> str:
        """
        Generates a text completion for a given prompt and optional system instructions.
        """
        pass
