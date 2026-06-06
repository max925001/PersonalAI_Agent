import asyncio
from typing import Optional
import google.generativeai as genai
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings
from app.core.exceptions import ChatException
from app.application.interfaces.llm_port import ILLMPort

class GeminiLlmAdapter(ILLMPort):
    """Adapter for Google Gemini LLM using the official GenerativeAI SDK."""

    def __init__(self):
        # Configure API key
        api_key = settings.GEMINI_API_KEY
        if not api_key or api_key == "gemini-key":
            api_key = settings.GOOGLE_API_KEY

        if not api_key or api_key == "gemini-key":
            logger.warning("Neither GEMINI_API_KEY nor GOOGLE_API_KEY is configured correctly. LLM calls will fail.")
        else:
            genai.configure(api_key=api_key)
            
        self.model_name = "models/gemini-2.5-flash"  # Fast and highly accurate for RAG summaries
        logger.info(f"Gemini LLM Adapter initialized using model: {self.model_name}")

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1.5, min=2, max=15),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    async def _generate_content_sync(
        self,
        prompt: str,
        system_instruction: Optional[str],
        temperature: float,
        max_output_tokens: Optional[int]
    ) -> str:
        loop = asyncio.get_running_loop()
        
        # Configure parameters
        config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens
        )
        
        model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_instruction
        )
        
        logger.info(f"Sending prompt to Gemini model '{self.model_name}' (temp={temperature})...")
        
        # Run synchronous call in worker thread to prevent event loop blocks
        response = await loop.run_in_executor(
            None,
            lambda: model.generate_content(
                contents=prompt,
                generation_config=config
            )
        )
        
        if not response or not response.text:
            raise Exception("Gemini LLM API returned empty or invalid response")
            
        return response.text

    async def generate_response(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.0,
        max_output_tokens: Optional[int] = None
    ) -> str:
        if not prompt:
            return ""
            
        try:
            return await self._generate_content_sync(prompt, system_instruction, temperature, max_output_tokens)
        except Exception as e:
            logger.error(f"Gemini LLM response generation failed: {str(e)}")
            raise ChatException(f"Failed to generate response from Gemini API: {str(e)}")
