import asyncio
from typing import Optional
import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings
from app.core.exceptions import ChatException
from app.application.interfaces.llm_port import ILLMPort

class GroqLlmAdapter(ILLMPort):
    """Adapter for Groq Cloud API using standard async HTTPX client."""

    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.model_name = settings.GROQ_MODEL
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self._client = httpx.AsyncClient(timeout=30.0)
        
        if not self.api_key or self.api_key == "groq-key":
            logger.warning("GROQ_API_KEY is not configured correctly. LLM calls will fail.")
        else:
            logger.info(f"Groq LLM Adapter initialized using model: {self.model_name}")

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
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
        }
        if max_output_tokens:
            payload["max_tokens"] = max_output_tokens
            
        logger.info(f"Sending request to Groq model '{self.model_name}'...")
        
        response = await self._client.post(self.api_url, headers=headers, json=payload)
        if response.status_code != 200:
            error_msg = f"Groq API returned status {response.status_code}: {response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
            
        response_json = response.json()
        try:
            text = response_json["choices"][0]["message"]["content"]
            if not text:
                raise Exception("Groq API returned empty completion content")
            return text
        except (KeyError, IndexError) as e:
            logger.error(f"Failed to parse Groq response: {response.text}")
            raise Exception(f"Failed to parse response format from Groq: {repr(e)}")

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
            logger.error(f"Groq LLM response generation failed: {str(e)}")
            raise ChatException(f"Failed to generate response from Groq API: {str(e)}")
