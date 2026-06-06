import asyncio
import struct
import time
from typing import Callable, Awaitable, Dict, Optional
from loguru import logger

from app.infrastructure.adapters.voice.whisper_stt_adapter import WhisperSttAdapter
from app.infrastructure.adapters.voice.piper_tts_adapter import PiperTtsAdapter
from app.application.agent.agent_use_case import AgentUseCase
from app.core.audio_utils import ulaw_to_pcm, resample_pcm_8k_to_16k, mp3_to_ulaw_8k

class TwilioVoicePipeline:
    """Coordinates incoming Twilio audio streams, transcribes voice, runs LLM, and streams back voice responses."""

    def __init__(self, agent_use_case: AgentUseCase):
        self.stt_adapter = WhisperSttAdapter()
        self.tts_adapter = PiperTtsAdapter()
        self.agent_use_case = agent_use_case
        
        # State management for active calls
        self.active_stream_tasks: Dict[str, asyncio.Task] = {}
        self.audio_buffers: Dict[str, bytearray] = {}
        self.user_is_speaking: Dict[str, bool] = {}
        self.silence_starts: Dict[str, Optional[float]] = {}
        self.is_ai_speaking: Dict[str, bool] = {}

    def cleanup_call(self, call_sid: str):
        """Cleans up internal state for a completed call."""
        logger.info(f"Cleaning up Twilio pipeline state for CallSid: {call_sid}")
        if call_sid in self.active_stream_tasks:
            self.active_stream_tasks[call_sid].cancel()
            del self.active_stream_tasks[call_sid]
        if call_sid in self.audio_buffers:
            del self.audio_buffers[call_sid]
        if call_sid in self.user_is_speaking:
            del self.user_is_speaking[call_sid]
        if call_sid in self.silence_starts:
            del self.silence_starts[call_sid]
        if call_sid in self.is_ai_speaking:
            del self.is_ai_speaking[call_sid]

    async def trigger_greeting(
        self,
        call_sid: str,
        conversation_id: str,
        send_outbound_audio: Callable[[bytes], Awaitable[None]]
    ):
        """Generates and plays the greeting when the call connects."""
        logger.info(f"Triggering greeting for CallSid: {call_sid}")
        self.cleanup_call(call_sid)
        
        # Start active greeting streaming task
        task = asyncio.create_task(
            self._generate_and_stream_response(
                call_sid=call_sid,
                conversation_id=conversation_id,
                text_input="hello",
                send_outbound_audio=send_outbound_audio
            )
        )
        self.active_stream_tasks[call_sid] = task

    async def process_inbound_chunk(
        self,
        call_sid: str,
        conversation_id: str,
        ulaw_chunk: bytes,
        send_outbound_audio: Callable[[bytes], Awaitable[None]],
        send_clear: Callable[[], Awaitable[None]]
    ):
        """Processes a 20ms mulaw chunk from Twilio, run VAD and manages interruptions."""
        if call_sid not in self.audio_buffers:
            self.audio_buffers[call_sid] = bytearray()
            self.user_is_speaking[call_sid] = False
            self.silence_starts[call_sid] = None
            self.is_ai_speaking[call_sid] = False

        # 1. Convert chunk to PCM and calculate RMS volume for VAD
        pcm_chunk = ulaw_to_pcm(ulaw_chunk)
        samples = struct.unpack(f"<{len(pcm_chunk)//2}h", pcm_chunk)
        
        sum_squares = sum((s / 32768.0) ** 2 for s in samples)
        rms = (sum_squares / len(samples)) ** 0.5 if samples else 0.0
        
        rms_threshold = 0.015
        silence_timeout = 1.2 # 1.2 seconds of silence triggers response
        
        if rms > rms_threshold:
            # User is speaking
            # Check for Interruption (AI is currently speaking)
            if self.is_ai_speaking.get(call_sid, False) or call_sid in self.active_stream_tasks:
                logger.info(f"User interruption detected on CallSid {call_sid} (RMS: {rms:.4f})! Clearing AI stream.")
                if call_sid in self.active_stream_tasks:
                    self.active_stream_tasks[call_sid].cancel()
                    del self.active_stream_tasks[call_sid]
                self.is_ai_speaking[call_sid] = False
                await send_clear()  # Tell Twilio to stop playing immediately
                
            self.user_is_speaking[call_sid] = True
            self.silence_starts[call_sid] = None
            self.audio_buffers[call_sid].extend(ulaw_chunk)
            
        else:
            # User is silent
            if self.user_is_speaking[call_sid]:
                if self.silence_starts[call_sid] is None:
                    self.silence_starts[call_sid] = time.time()
                elif time.time() - self.silence_starts[call_sid] > silence_timeout:
                    # User finished speaking, trigger response generation
                    logger.info(f"Silence timeout met on CallSid {call_sid}. Triggering response generation.")
                    user_audio = bytes(self.audio_buffers[call_sid])
                    
                    # Reset buffer/state
                    self.audio_buffers[call_sid] = bytearray()
                    self.user_is_speaking[call_sid] = False
                    self.silence_starts[call_sid] = None
                    
                    # Start async task to handle transcription and response
                    task = asyncio.create_task(
                        self._process_speech_and_respond(
                            call_sid=call_sid,
                            conversation_id=conversation_id,
                            user_audio=user_audio,
                            send_outbound_audio=send_outbound_audio
                        )
                    )
                    self.active_stream_tasks[call_sid] = task

    async def _process_speech_and_respond(
        self,
        call_sid: str,
        conversation_id: str,
        user_audio: bytes,
        send_outbound_audio: Callable[[bytes], Awaitable[None]]
    ):
        """Helper to run voice transcription, LLM agent, and TTS playback."""
        try:
            # 1. Transcode 8kHz Mu-law to 16kHz linear PCM for Whisper
            pcm_8k = ulaw_to_pcm(user_audio)
            pcm_16k = resample_pcm_8k_to_16k(pcm_8k)
            
            # 2. Speech to Text (Whisper)
            logger.info(f"Sending audio to Whisper STT for CallSid: {call_sid}")
            transcript = await self.stt_adapter.transcribe(pcm_16k)
            logger.info(f"Whisper transcript: '{transcript}'")
            
            if not transcript or transcript.strip() == "":
                logger.info("Empty transcript. Ignoring voice trigger.")
                return
                
            # 3. Generate response and play
            await self._generate_and_stream_response(
                call_sid=call_sid,
                conversation_id=conversation_id,
                text_input=transcript,
                send_outbound_audio=send_outbound_audio
            )
            
        except asyncio.CancelledError:
            logger.info(f"Voice execution cancelled for CallSid {call_sid} (Interrupted).")
        except Exception as e:
            logger.exception(f"Error in speech responder pipeline for CallSid {call_sid}: {e}")

    async def _generate_and_stream_response(
        self,
        call_sid: str,
        conversation_id: str,
        text_input: str,
        send_outbound_audio: Callable[[bytes], Awaitable[None]]
    ):
        """Executes LangGraph agent, synthesizes speech to MP3, transcodes to Mu-law, and streams to Twilio."""
        try:
            # 1. Run LangGraph Agent Node execution
            logger.info(f"Executing AgentUseCase for CallSid: {call_sid}")
            result = await self.agent_use_case.execute(
                session_id=conversation_id,
                message=text_input,
                voice_mode=True
            )
            response_text = result["response"]
            logger.info(f"Agent response: '{response_text}'")
            
            # 2. Text to Speech (Edge-TTS)
            logger.info(f"Synthesizing response via Edge-TTS for CallSid: {call_sid}")
            mp3_audio = await self.tts_adapter.synthesize(response_text)
            
            if not mp3_audio:
                logger.warning("No audio generated by TTS. Skipping outbound playback.")
                return
                
            # 3. Transcode MP3 to Mu-law (8kHz 8-bit Mono)
            ulaw_audio = mp3_to_ulaw_8k(mp3_audio)
            
            # 4. Stream to Twilio in 20ms chunks (160 bytes of mulaw)
            logger.info(f"Streaming {len(ulaw_audio)} bytes of Mu-law audio to CallSid: {call_sid}")
            self.is_ai_speaking[call_sid] = True
            
            chunk_size = 160
            for i in range(0, len(ulaw_audio), chunk_size):
                chunk = ulaw_audio[i : i + chunk_size]
                if len(chunk) < chunk_size:
                    # Pad silence (0xFF represents silence in G.711 mulaw)
                    chunk += b"\xFF" * (chunk_size - len(chunk))
                    
                await send_outbound_audio(chunk)
                await asyncio.sleep(0.02) # 20ms pacing
                
            self.is_ai_speaking[call_sid] = False
            logger.info(f"Finished streaming audio response to CallSid: {call_sid}")
            
        except asyncio.CancelledError:
            logger.info(f"Audio response streaming cancelled for CallSid {call_sid} (Interrupted).")
            self.is_ai_speaking[call_sid] = False
        finally:
            if call_sid in self.active_stream_tasks:
                del self.active_stream_tasks[call_sid]
