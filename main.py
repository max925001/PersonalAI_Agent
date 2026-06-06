import sys
if sys.platform == "win32":
    import ssl
    import certifi
    
    _original_create_default_context = ssl.create_default_context
    
    def patched_create_default_context(purpose=ssl.Purpose.SERVER_AUTH, *, cafile=None, capath=None, cadata=None):
        if cafile is None and capath is None and cadata is None:
            cafile = certifi.where()
        return _original_create_default_context(purpose, cafile=cafile, capath=capath, cadata=cadata)
        
    ssl.create_default_context = patched_create_default_context

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.exceptions import AppException
from app.infrastructure.persistence.mongodb.database import init_database, close_connections
from app.infrastructure.web.router import api_router
from loguru import logger

setup_logging()

async def keep_alive_task():
    """Periodically pings the public URL to keep Render instance awake."""
    import asyncio
    await asyncio.sleep(15)  # Wait for startup to complete
    if settings.APP_ENV != "production" or not settings.PUBLIC_URL:
        logger.info("Keep-alive task disabled (not in production or PUBLIC_URL is not set).")
        return
        
    logger.info(f"Keep-alive task started. Target: {settings.PUBLIC_URL}")
    import httpx
    async with httpx.AsyncClient() as client:
        while True:
            try:
                url = f"{settings.PUBLIC_URL.rstrip('/')}/health"
                logger.info(f"Sending keep-alive ping to: {url}")
                res = await client.get(url, timeout=15.0)
                logger.info(f"Keep-alive ping response: {res.status_code}")
            except Exception as e:
                logger.warning(f"Keep-alive ping failed: {e}")
            await asyncio.sleep(600)  # Ping every 10 minutes (600 seconds)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize MongoDB and Beanie
    await init_database()
    
    # Start background keep-alive task to prevent Render sleep mode
    import asyncio
    keep_alive_loop = asyncio.create_task(keep_alive_task())
    
    yield
    # Shutdown: Close database pools
    keep_alive_loop.cancel()
    close_connections()

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan
)

# Configure CORS to allow local development origins with credentials
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

if settings.PUBLIC_URL:
    public_url_clean = settings.PUBLIC_URL.strip().rstrip("/")
    if public_url_clean.startswith("https://"):
        origins.append(public_url_clean)
        origins.append(public_url_clean.replace("https://", "http://"))
    elif public_url_clean.startswith("http://"):
        origins.append(public_url_clean)
        origins.append(public_url_clean.replace("http://", "https://"))
    else:
        origins.append(f"https://{public_url_clean}")
        origins.append(f"http://{public_url_clean}")

if settings.FRONTEND_URL:
    frontend_url_clean = settings.FRONTEND_URL.strip().rstrip("/")
    if frontend_url_clean.startswith("https://"):
        origins.append(frontend_url_clean)
        origins.append(frontend_url_clean.replace("https://", "http://"))
    elif frontend_url_clean.startswith("http://"):
        origins.append(frontend_url_clean)
        origins.append(frontend_url_clean.replace("http://", "https://"))
    else:
        origins.append(f"https://{frontend_url_clean}")
        origins.append(f"http://{frontend_url_clean}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    logger.warning(f"AppException [{exc.code}]: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "code": exc.code
        }
    )

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    logger.warning(f"ValueError: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": str(exc),
            "code": "VALIDATION_FAILED"
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.exception("An unhandled exception occurred")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected error occurred. Please try again later.",
            "code": "INTERNAL_SERVER_ERROR"
        }
    )

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

app.include_router(api_router, prefix=settings.API_V1_PREFIX)

if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)