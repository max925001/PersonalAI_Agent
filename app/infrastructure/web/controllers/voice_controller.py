import base64
import json
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from loguru import logger

from app.application.agent.agent_use_case import AgentUseCase
from app.infrastructure.adapters.voice.whisper_stt_adapter import WhisperSttAdapter
from app.infrastructure.adapters.voice.piper_tts_adapter import PiperTtsAdapter
from app.infrastructure.web.dependencies import get_agent_use_case

router = APIRouter()

# Instantiate adapters
stt_adapter = WhisperSttAdapter()
tts_adapter = PiperTtsAdapter()

@router.websocket("/stream")
async def voice_stream(
    websocket: WebSocket,
    agent_use_case: AgentUseCase = Depends(get_agent_use_case)
):
    """
    WebSocket endpoint for real-time voice chat.
    Recruiter connects, clicks "START TALKING", streams PCM audio,
    and receives transcribed text, agent reply, and synthesized speech audio.
    """
    await websocket.accept()
    session_id = str(uuid.uuid4())
    logger.info(f"Voice WebSocket connection accepted. Session ID: {session_id}")
    
    # Store raw PCM bytes accumulated during recruiter's active speech turn
    audio_buffer = bytearray()
    
    try:
        # Send initial confirmation event
        await websocket.send_json({
            "event": "session_started",
            "session_id": session_id
        })
        
        while True:
            # Await text/json message from recruiter client
            data = await websocket.receive_text()
            payload = json.loads(data)
            event_type = payload.get("event")
            
            if event_type == "start_talking":
                logger.info(f"Recruiter session {session_id} started talking. Triggering greeting.")
                await websocket.send_json({"event": "agent_thinking"})
                
                # Fetch Shivam's representative greeting
                result = await agent_use_case.execute(session_id=session_id, message="hello", voice_mode=True)
                response_text = result["response"]
                
                # Synthesize greeting speech
                audio_fallback = False
                base64_audio = ""
                try:
                    audio_bytes = await tts_adapter.synthesize(response_text)
                    if audio_bytes:
                        base64_audio = base64.b64encode(audio_bytes).decode("utf-8")
                    else:
                        audio_fallback = True
                except Exception as tts_err:
                    logger.warning(f"TTS synthesis failed, falling back to client-side speech: {tts_err}")
                    audio_fallback = True
                
                await websocket.send_json({
                    "event": "agent_response_text",
                    "text": response_text,
                    "audio_fallback": audio_fallback
                })
                if base64_audio:
                    await websocket.send_json({
                        "event": "audio_chunk",
                        "audio": base64_audio
                    })
                
            elif event_type == "audio_chunk":
                # Decode base64 PCM bytes and append to active speech buffer
                base64_data = payload.get("audio", "")
                if base64_data:
                    chunk = base64.b64decode(base64_data)
                    audio_buffer.extend(chunk)
                    
            elif event_type == "speech_done":
                # Recruiter stopped speaking. Run transcription (STT) -> Agent -> Speech synthesis (TTS)
                logger.info(f"Recruiter speech turn complete. Processing buffer of size: {len(audio_buffer)} bytes")
                if len(audio_buffer) == 0:
                    await websocket.send_json({
                        "event": "transcript",
                        "text": "[Silence]",
                        "status": "final"
                    })
                    continue
                
                # Step 1: Speech to Text (Whisper)
                transcript = await stt_adapter.transcribe(bytes(audio_buffer))
                # Clear buffer for next turn
                audio_buffer.clear()
                
                if not transcript or transcript.strip() == "":
                    await websocket.send_json({
                        "event": "transcript",
                        "text": "[Silence]",
                        "status": "final"
                    })
                    await websocket.send_json({
                        "event": "silence_detected"
                    })
                    continue
                
                await websocket.send_json({
                    "event": "transcript",
                    "text": transcript,
                    "status": "final"
                })
                
                # Step 2: LangGraph Agent Node execution
                await websocket.send_json({"event": "agent_thinking"})
                result = await agent_use_case.execute(session_id=session_id, message=transcript, voice_mode=True)
                response_text = result["response"]
                
                # Step 3: Text to Speech (Piper)
                audio_fallback = False
                base64_audio = ""
                try:
                    audio_bytes = await tts_adapter.synthesize(response_text)
                    if audio_bytes:
                        base64_audio = base64.b64encode(audio_bytes).decode("utf-8")
                    else:
                        audio_fallback = True
                except Exception as tts_err:
                    logger.warning(f"TTS synthesis failed, falling back to client-side speech: {tts_err}")
                    audio_fallback = True
                
                await websocket.send_json({
                    "event": "agent_response_text",
                    "text": response_text,
                    "audio_fallback": audio_fallback
                })
                if base64_audio:
                    await websocket.send_json({
                        "event": "audio_chunk",
                        "audio": base64_audio
                    })
                
            elif event_type == "text_message":
                # Text fallback path
                text_query = payload.get("text", "")
                logger.info(f"Recruiter sent text override: '{text_query}'")
                
                await websocket.send_json({"event": "agent_thinking"})
                result = await agent_use_case.execute(session_id=session_id, message=text_query, voice_mode=True)
                response_text = result["response"]
                
                audio_fallback = False
                base64_audio = ""
                try:
                    audio_bytes = await tts_adapter.synthesize(response_text)
                    if audio_bytes:
                        base64_audio = base64.b64encode(audio_bytes).decode("utf-8")
                    else:
                        audio_fallback = True
                except Exception as tts_err:
                    logger.warning(f"TTS synthesis failed, falling back to client-side speech: {tts_err}")
                    audio_fallback = True
                
                await websocket.send_json({
                    "event": "agent_response_text",
                    "text": response_text,
                    "audio_fallback": audio_fallback
                })
                if base64_audio:
                    await websocket.send_json({
                        "event": "audio_chunk",
                        "audio": base64_audio
                    })
                
            elif event_type == "end_session":
                logger.info(f"Recruiter ended session: {session_id}")
                await websocket.send_json({"event": "session_ended"})
                break
                
    except WebSocketDisconnect:
        logger.info(f"Voice WebSocket disconnected for session: {session_id}")
    except Exception as e:
        logger.exception(f"Error handling voice websocket session: {session_id}")
        try:
            await websocket.send_json({
                "event": "error",
                "message": f"An error occurred: {str(e)}"
            })
        except:
            pass
