import edge_tts
from loguru import logger
from app.application.interfaces.speech_port import ITextToSpeechPort

class PiperTtsAdapter(ITextToSpeechPort):
    """
    Adapter implementing Text-to-Speech using free Microsoft Edge Neural TTS.
    Returns high-quality voice audio as MP3 bytes.
    """
    
    def __init__(self):
        # en-IN-PrabhatNeural is a highly realistic Indian English male voice
        self.voice = "en-IN-PrabhatNeural"
        logger.info(f"EdgeTTS Adapter initialized. Voice: {self.voice}")

    async def synthesize(self, text: str) -> bytes:
        logger.info(f"EdgeTTS synthesizing text: '{text[:50]}...'")
        
        # Clean text of asterisks and other markdown before speech synthesis
        cleaned_text = text.replace("*", "").replace("#", "").strip()
        
        if not cleaned_text:
            return b""
            
        try:
            communicate = edge_tts.Communicate(cleaned_text, self.voice)
            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
            return audio_data
        except Exception as e:
            logger.error(f"EdgeTTS synthesis failed: {e}")
            raise e
