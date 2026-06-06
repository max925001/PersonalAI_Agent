import asyncio
import httpx
from loguru import logger
from app.application.interfaces.speech_port import ISpeechToTextPort
from app.core.config import settings

def create_wav_header(pcm_data_len: int, sample_rate: int = 16000, num_channels: int = 1, bits_per_sample: int = 16) -> bytes:
    header = bytearray(44)
    # RIFF descriptor
    header[0:4] = b'RIFF'
    file_size = pcm_data_len + 36
    header[4:8] = file_size.to_bytes(4, 'little')
    header[8:12] = b'WAVE'
    
    # fmt chunk
    header[12:16] = b'fmt '
    header[16:20] = (16).to_bytes(4, 'little')
    header[20:22] = (1).to_bytes(2, 'little')  # PCM format
    header[22:24] = num_channels.to_bytes(2, 'little')
    header[24:28] = sample_rate.to_bytes(4, 'little')
    
    byte_rate = int(sample_rate * num_channels * bits_per_sample / 8)
    header[28:32] = byte_rate.to_bytes(4, 'little')
    
    block_align = int(num_channels * bits_per_sample / 8)
    header[32:34] = block_align.to_bytes(2, 'little')
    
    header[34:36] = bits_per_sample.to_bytes(2, 'little')
    
    # data chunk
    header[36:40] = b'data'
    header[40:44] = pcm_data_len.to_bytes(4, 'little')
    
    return bytes(header)

class WhisperSttAdapter(ISpeechToTextPort):
    """
    Adapter implementing Speech-to-Text using Groq Cloud's Whisper API.
    Converts raw 16kHz PCM audio bytes to WAV and transcribes using whisper-large-v3.
    """
    
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.api_url = "https://api.groq.com/openai/v1/audio/transcriptions"
        self._client = httpx.AsyncClient(timeout=15.0)
        logger.info("Whisper STT Adapter initialized with Groq Whisper API.")

    async def transcribe(self, audio_bytes: bytes) -> str:
        logger.info(f"Whisper transcribing audio chunk of size: {len(audio_bytes)} bytes")
        
        if not self.api_key or self.api_key == "groq-key":
            logger.warning("GROQ_API_KEY is not configured. Falling back to simulated prompt.")
            await asyncio.sleep(0.4)
            return "tell me about shivam's experience"

        try:
            # 1. Prepend valid WAV header to PCM bytes
            wav_header = create_wav_header(len(audio_bytes), sample_rate=16000, num_channels=1, bits_per_sample=16)
            wav_data = wav_header + audio_bytes
            
            # 2. Call Groq Whisper API via async multipart/form-data
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }
            files = {
                "file": ("speech.wav", wav_data, "audio/wav")
            }
            data = {
                "model": "whisper-large-v3",
                "response_format": "json"
            }
            
            logger.info("Sending transcription request to Groq Whisper API...")
            response = await self._client.post(self.api_url, headers=headers, files=files, data=data)
            
            if response.status_code != 200:
                logger.warning(f"Groq Whisper API returned error {response.status_code}: {response.text}. Falling back to empty.")
                return ""
                
            res_json = response.json()
            transcript = res_json.get("text", "").strip()
            
            # Filter common Whisper silence hallucinations
            hallucination_phrases = {
                "thank you for watching",
                "thank you for watching.",
                "thank you for watching this video",
                "thank you for watching this video.",
                "thanks for watching",
                "thanks for watching.",
                "thank you.",
                "thank you",
                "you",
                "you.",
                "please subscribe",
                "subscribe"
            }
            
            clean_transcript = transcript.lower().strip(" .!,")
            if not transcript or clean_transcript in hallucination_phrases or len(clean_transcript) <= 1:
                logger.info(f"Whisper STT detected silence/hallucination: '{transcript}'. Returning empty transcript.")
                return ""
                
            logger.info(f"Whisper STT transcription success: '{transcript}'")
            return transcript
            
        except Exception as e:
            logger.exception("Failed to call Groq Whisper API. Falling back to empty.")
            return ""
