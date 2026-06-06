import base64
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from loguru import logger

from app.application.voice.call_session_service import CallSessionService
from app.application.voice.twilio_voice_pipeline import TwilioVoicePipeline
from app.infrastructure.web.dependencies import get_call_session_service, get_twilio_voice_pipeline

router = APIRouter()

@router.websocket("/stream")
async def twilio_stream(
    websocket: WebSocket,
    call_session_service: CallSessionService = Depends(get_call_session_service),
    twilio_voice_pipeline: TwilioVoicePipeline = Depends(get_twilio_voice_pipeline)
):
    """
    WebSocket endpoint for real-time Twilio voice streaming (8kHz Mu-law).
    Twilio connects to this route after receiving the TwiML response.
    """
    await websocket.accept()
    logger.info("Twilio voice WebSocket connection accepted.")
    
    stream_sid = None
    call_sid = None
    conversation_id = None
    
    # Callback to send processed audio chunks back to Twilio
    async def send_outbound_audio(chunk: bytes):
        if stream_sid and websocket:
            payload = base64.b64encode(chunk).decode("utf-8")
            try:
                await websocket.send_json({
                    "event": "media",
                    "streamSid": stream_sid,
                    "media": {
                        "payload": payload
                    }
                })
            except Exception as e:
                logger.error(f"Failed to send audio chunk to Twilio: {e}")

    # Callback to clear Twilio's audio playback buffer on user barge-in/interruption
    async def send_clear():
        if stream_sid and websocket:
            try:
                logger.info(f"Sending CLEAR event to Twilio StreamSid: {stream_sid}")
                await websocket.send_json({
                    "event": "clear",
                    "streamSid": stream_sid
                })
            except Exception as e:
                logger.error(f"Failed to send clear event to Twilio: {e}")

    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            event_type = payload.get("event")
            
            if event_type == "start":
                # Connection started, retrieve SID values
                stream_sid = payload.get("streamSid")
                start_data = payload.get("start", {})
                call_sid = start_data.get("callSid")
                logger.info(f"Twilio stream started. StreamSid: {stream_sid} | CallSid: {call_sid}")
                
                # Fetch Call Session from MongoDB to link conversation memory ID
                session = await call_session_service.get_session_by_sid(call_sid)
                if not session:
                    logger.error(f"No registered session found in MongoDB for CallSid: {call_sid}")
                    await websocket.close()
                    return
                    
                conversation_id = str(session.conversation_id)
                await call_session_service.update_session_state(call_sid, "CALL_CONNECTED")
                
                # Trigger greeting speech
                await twilio_voice_pipeline.trigger_greeting(
                    call_sid=call_sid,
                    conversation_id=conversation_id,
                    send_outbound_audio=send_outbound_audio
                )
                
            elif event_type == "media":
                # Incoming audio chunk payload from the recruiter (8kHz 8-bit Mono Mu-law)
                media = payload.get("media", {})
                payload_b64 = media.get("payload", "")
                if payload_b64 and call_sid:
                    raw_chunk = base64.b64decode(payload_b64)
                    
                    # Process chunk through the voice pipeline VAD & interruption loop
                    await twilio_voice_pipeline.process_inbound_chunk(
                        call_sid=call_sid,
                        conversation_id=conversation_id,
                        ulaw_chunk=raw_chunk,
                        send_outbound_audio=send_outbound_audio,
                        send_clear=send_clear
                    )
                    
            elif event_type == "stop":
                logger.info(f"Twilio stream stop event received. CallSid: {call_sid}")
                break
                
    except WebSocketDisconnect:
        logger.info(f"Twilio voice WebSocket disconnected.")
    except Exception as e:
        logger.exception(f"Exception encountered in Twilio voice streaming: {e}")
    finally:
        if call_sid:
            # Complete the call state in MongoDB
            await call_session_service.update_session_state(call_sid, "COMPLETED")
            twilio_voice_pipeline.cleanup_call(call_sid)
