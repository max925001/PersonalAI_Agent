from abc import ABC, abstractmethod

class ISpeechToTextPort(ABC):
    """Port contract for Speech-to-Text translation (STT)."""
    @abstractmethod
    async def transcribe(self, audio_bytes: bytes) -> str:
        """Transcribes raw audio bytes into text."""
        pass

class ITextToSpeechPort(ABC):
    """Port contract for Text-to-Speech synthesis (TTS)."""
    @abstractmethod
    async def synthesize(self, text: str) -> bytes:
        """Synthesizes text into raw PCM audio bytes."""
        pass
