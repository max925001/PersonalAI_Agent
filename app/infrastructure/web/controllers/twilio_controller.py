from fastapi import APIRouter, Form, Request, Response, Depends
from loguru import logger
from app.application.voice.call_session_service import CallSessionService
from app.core.config import settings
from app.infrastructure.web.dependencies import get_call_session_service

router = APIRouter()

@router.post("/incoming-call")
async def handle_incoming_call(
    request: Request,
    CallSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...),
    call_session_service: CallSessionService = Depends(get_call_session_service)
):
    """
    Webhook endpoint answering Twilio incoming voice calls.
    Returns TwiML instructing Twilio to pipe call audio to our WebSocket stream.
    """
    logger.info(f"Incoming call webhook received. CallSid: {CallSid} | From: {From} | To: {To}")
    
    # 1. Register Call Session in MongoDB Atlas
    await call_session_service.create_session(
        call_sid=CallSid,
        from_number=From,
        to_number=To
    )
    
    # 2. Determine WebSocket Host (Public address or local fallback)
    # Using request headers or a dedicated setting to handle SSL proxies correctly
    if settings.PUBLIC_URL:
        from urllib.parse import urlparse
        parsed = urlparse(settings.PUBLIC_URL)
        host = parsed.netloc
        scheme = "wss" if parsed.scheme == "https" else "ws"
    else:
        host = request.headers.get("x-forwarded-host") or request.url.netloc
        scheme = "wss" if request.headers.get("x-forwarded-proto") == "https" or "ngrok" in host else "ws"
    
    websocket_stream_url = f"{scheme}://{host}/api/v1/voice/twilio/stream"
    logger.info(f"Directing Twilio CallSid {CallSid} to WebSocket stream: {websocket_stream_url}")
    
    # 3. Generate TwiML Connect Stream instruction
    twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Connecting to Shivam's digital representative.</Say>
    <Connect>
        <Stream url="{websocket_stream_url}" />
    </Connect>
</Response>
"""
    return Response(content=twiml_response, media_type="application/xml")
