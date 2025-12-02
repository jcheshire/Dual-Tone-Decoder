from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from core.database import init_db
from core.rate_limit import limiter
from api import tone_entries, audio_upload


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database
    await init_db()
    yield
    # Shutdown: cleanup if needed


app = FastAPI(
    title="Dual-Tone Decoder",
    description="Web-based tool for decoding two-tone sequential paging signals",
    version="1.0.0",
    lifespan=lifespan
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Include API routers
app.include_router(tone_entries.router)
app.include_router(audio_upload.router)


@app.get("/health")
@limiter.limit("60/minute")  # Allow 60 health checks per minute
async def health_check(request: Request):
    """Health check endpoint."""
    return {"status": "healthy"}
