from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from backend.core.database import init_db
from backend.api import tone_entries, audio_upload


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

# Include API routers
app.include_router(tone_entries.router)
app.include_router(audio_upload.router)

# Mount static files
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")


@app.get("/")
async def read_root():
    """Serve the main HTML page."""
    return FileResponse("frontend/templates/index.html")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
