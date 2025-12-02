from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pathlib import Path
import os
import uuid
import re
from typing import List
from backend.core.database import get_db
from backend.core.config import get_settings
from backend.core.rate_limit import limiter
from backend.models.tone_table import ToneEntry
from backend.models.schemas import ToneDetectionResult, ToneEntryResponse
from backend.services.tone_detector import ToneDetector

router = APIRouter(prefix="/api/decode", tags=["audio"])
settings = get_settings()

# Whitelist of safe file extensions (no path traversal characters)
SAFE_EXTENSIONS = {'.wav'}


@router.post("/", response_model=ToneDetectionResult)
@limiter.limit("10/minute")  # Limit to 10 audio uploads per minute per IP
async def decode_audio(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload an audio file and detect two-tone sequence.
    Rate limited to 10 requests per minute per IP address.
    """
    # Sanitize and validate filename to prevent path traversal
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided"
        )

    # Extract extension safely - use only the last component
    original_filename = os.path.basename(file.filename)  # Remove any path components
    file_ext = os.path.splitext(original_filename)[1].lower()

    # Strict whitelist validation (not from config to prevent manipulation)
    if file_ext not in SAFE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Only WAV files are allowed."
        )

    # Validate file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning

    max_size = settings.max_file_size_mb * 1024 * 1024
    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Max size: {settings.max_file_size_mb}MB"
        )

    # Save uploaded file temporarily with secure filename
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Use only UUID for filename (no user input in path)
    temp_filename = f"{uuid.uuid4()}.wav"
    temp_path = upload_dir / temp_filename

    # Verify the path is still within upload_dir (defense in depth)
    if not temp_path.resolve().is_relative_to(upload_dir.resolve()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file path"
        )

    try:
        # Write file with size limit enforcement during read
        bytes_written = 0
        max_bytes = max_size

        with open(temp_path, "wb") as f:
            # Read in chunks to avoid loading entire file into memory
            chunk_size = 1024 * 1024  # 1MB chunks
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break

                bytes_written += len(chunk)
                if bytes_written > max_bytes:
                    # Clean up partial file
                    f.close()
                    if temp_path.exists():
                        os.remove(temp_path)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File too large. Max size: {settings.max_file_size_mb}MB"
                    )

                f.write(chunk)

        # Detect tones
        detector = ToneDetector(tolerance_hz=settings.frequency_tolerance_hz)
        tone1_hz, tone2_hz, confidence = detector.detect_two_tone_sequence(str(temp_path))

        if tone1_hz is None or tone2_hz is None:
            return ToneDetectionResult(
                tone1_detected_hz=None,
                tone2_detected_hz=None,
                matched_entry=None,
                confidence=0.0,
                message="No two-tone sequence detected in audio file"
            )

        # Fetch all tone entries from database
        result = await db.execute(select(ToneEntry))
        entries = result.scalars().all()

        # Convert to format expected by detector
        tone_list = [(e.id, e.label, e.tone1_hz, e.tone2_hz) for e in entries]

        # Find matching entry
        matched = detector.find_matching_tone(tone1_hz, tone2_hz, tone_list)

        if matched:
            entry_id, label, _, _ = matched
            matched_entry_obj = next(e for e in entries if e.id == entry_id)
            matched_entry = ToneEntryResponse.model_validate(matched_entry_obj)
            message = f"Match found: {label}"
        else:
            matched_entry = None
            message = "Tones detected but no matching entry in database"

        return ToneDetectionResult(
            tone1_detected_hz=round(tone1_hz, 1),
            tone2_detected_hz=round(tone2_hz, 1),
            matched_entry=matched_entry,
            confidence=round(confidence, 2),
            message=message
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid audio file format"
        )
    except Exception as e:
        # Log the actual error for debugging but don't expose to user
        # TODO: Add proper logging here
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing audio file. Please ensure it is a valid WAV file."
        )
    finally:
        # Clean up temporary file
        try:
            if temp_path.exists():
                os.remove(temp_path)
        except Exception:
            # Log but don't fail if cleanup fails
            pass
