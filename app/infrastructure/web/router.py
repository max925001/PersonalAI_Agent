from fastapi import APIRouter
from app.infrastructure.web.controllers import (
    auth_controller,
    profile_controller,
    chat_controller,
    scheduling_controller,
    voice_controller,
    twilio_controller
)
from app.infrastructure.web.websocket import twilio_stream_handler

api_router = APIRouter()
api_router.include_router(auth_controller.router, prefix="/auth")
api_router.include_router(profile_controller.router, prefix="/admin")
api_router.include_router(chat_controller.router, prefix="/chat")
api_router.include_router(scheduling_controller.router, prefix="/scheduling")
api_router.include_router(voice_controller.router, prefix="/voice")
api_router.include_router(twilio_controller.router, prefix="/voice")
api_router.include_router(twilio_stream_handler.router, prefix="/voice/twilio")
